from dataclasses import dataclass, field as dfield
from pathlib import Path
from random import sample
from string import ascii_lowercase
from struct import Struct as CStruct
from typing import Any, Iterable, Optional, TypedDict

from rich.table import Table

from ayed.utils import build_cfn, console

ascii_lowercase = "".join(x for x in ascii_lowercase if x != "x")

C_DTYPES = {
    "char",
    "signed char",
    "unsigned char",
    "short",
    "short int",
    "signed short",
    "signed short int",
    "unsigned short",
    "unsigned short int",
    "int",
    "signed",
    "signed int",
    "unsigned",
    "unsigned int",
    "long",
    "long int",
    "signed long",
    "signed long int",
    "unsigned long",
    "unsigned long int",
    "long long",
    "long long int",
    "signed long long",
    "signed long long int",
    "unsigned long long",
    "unsigned long long int",
    "float",
    "double",
    "long double",
}


@dataclass
class Variable:
    type: str
    name: str
    ctype: Optional[int] = None
    data: list[Any] = dfield(
        default_factory=list
    )  # the data that the variable holds. Used when loading an excel file
    struct_id: Optional[int] = None
    file_id: Optional[int] = None

    def __post_init__(self):
        if self.type == "string":
            self.type = "std::string"

    def type_to_str(self) -> str:
        return (
            f"{self.type.lower()}ToString"
            if self.type not in C_DTYPES
            else ""  # if type not in C_DTYPES, either return '' or tToString
            if self.type == "char"
            else "std::to_string"
        )

    def str_to_type(self) -> str:
        if self.ctype:
            return "strcpy"
        return {"int": "stoi"}.get(self.type, f"{self.type.lower()}FromString")

    def format_character(self) -> str:
        if self.ctype:
            return f"{self.ctype}s"
        return {"int": "i", "long": "long", "double": "d"}.get(self.type, "c")


class File(TypedDict):
    filenames: list[str]
    structs: list[str]
    variables: list[Variable]


@dataclass
class Struct(Iterable[Variable]):
    name: str
    fields: tuple[Variable, ...]
    cstruct: CStruct = dfield(init=False)

    def __post_init__(self):
        c_fmt = "".join(ctype.format_character() for ctype in self.fields)
        self.cstruct = CStruct(c_fmt)

    def __iter__(self):
        yield from self.fields

    # TODO: Use a different separator when reading a struct
    def to_str(self, sep: Optional[str] = "-") -> str:
        name = self.name[0].lower()
        variables: list[str] = []
        for field in self:
            if field.type == "string":
                variables.append(field.name)
                continue
            s = f"{field.type_to_str()}({name}.{field.name})"
            variables.append(s)
        ret = f"+'{sep}'+".join(variables)
        return build_cfn(
            "std::string",
            f"{self.name.lower()}ToString",
            vret=ret,
            params=[f"{self.name} {name}"],
        )

    @property
    def size(self):
        return self.cstruct.size

    def pack(self, file_name: str, *, unpack: Optional[bool] = True) -> None:
        """Writes the raw bytes of the struct to `file_path`"""
        filepath = Path("output_files")
        if not filepath.exists():
            filepath.mkdir()
        filepath /= file_name
        data_len = len(self.fields[0].data)
        with filepath.open(mode="w+b") as dat:
            for i in range(data_len):
                data = [field.data[i] for field in self]
                bdata = self.cstruct.pack(*data)
                dat.write(bdata)
        if unpack:
            self.unpack(filepath)

    def unpack(self, filepath: Path) -> None:
        """Reads struct data written with `pack` from `filepath`"""
        if not filepath.exists():
            raise AssertionError("Path doesn't exist")
        data_len = len(self.fields[0].data)
        table = Table(
            highlight=True,
            title=f"{filepath.name} - {self.size * data_len} bytes",
            title_justify="center",
            show_header=True,
            show_lines=True,
        )
        for field in self:
            table.add_column(field.name, justify="center")
        with filepath.open("rb") as dat:
            while d := dat.read(self.size):
                written = self.cstruct.unpack(d)
                table.add_row(*[str(d) for d in written])
        console.print(table, justify="center")

    def from_str(self) -> str:
        variables: list[str] = [f"{self.name} x" + "{}"]
        for i, field in enumerate(self):
            token = f"std::string t{i} = getTokenAt(s, '-', {i})"
            variables.append(token)
            if fn := field.str_to_type():
                variables.append(
                    fn + f"(x.{field.name}, t{i}.c_str())"
                    if fn == "strcpy"
                    else f"x.{field.name} = {fn}(t{i})"
                )
        return build_cfn(
            self.name,
            f"{self.name.lower()}FromString",
            vret="x",
            params=["std::string s"],
            body=variables,
        )

    def to_debug(self) -> str:
        name = self.name.lower()[0]
        body = ["std::stringstream sout", f'sout << "{self.name}"' + ' << "{"']
        for i, field in enumerate(self):
            body.append(
                f'sout << "{field.name} : " << {name}.{field.name}'
                + (' << ", "' if i != len(self.fields) - 1 else "")
            )
        body.append('sout << "};"')
        return build_cfn(
            "std::string",
            f"{self.name.lower()}ToDebug",
            params=[f"{self.name} {name}"],
            body=body,
            vret="sout.str()",
        )

    def init(self) -> str:
        vnames = sample(ascii_lowercase[13:], k=len(self.fields))
        parameters = [
            f'{field.type if not field.ctype else "std::string"} {vnames[i]}'
            for i, field in enumerate(self)
        ]
        body: list[str] = [f"{self.name} x" + "{}"]
        for i, field in enumerate(self):
            if field.ctype:
                body.append(
                    f"{field.str_to_type()}(x.{field.name}, {vnames[i]}.c_str())"
                )
                continue
            line = f"x.{field.name} = {vnames[i]}"
            body.append(line)
        return build_cfn(
            self.name, f"new{self.name}", vret="x", params=parameters, body=body
        )

    def __str__(self) -> str:
        fns = f"struct {self.name} " + "{\n"
        for field in self:
            fns += f"  {field.type} {field.name}" + (
                f"[{field.ctype}];\n" if field.ctype else ";\n"
            )
        fns += "};\n"
        return fns
