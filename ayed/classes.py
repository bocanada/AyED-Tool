from pathlib import Path
from random import sample
from string import ascii_lowercase
from struct import Struct as CStruct
from typing import Any, Iterable, Optional

from attr import Factory, dataclass
from attr import field as dfield

from ayed.utils import build_cfn, console, create_table

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


@dataclass(slots=True, str=False)
class Variable:
    type: str
    name: str
    ctype: Optional[int] = dfield(
        default=0, validator=lambda __, _, v: v is not None and isinstance(v, int)
    )
    data: list[Any] = Factory(list)
    struct_id: Optional[int] = dfield(init=False, default=None, repr=False)
    file_id: Optional[int] = dfield(init=False, default=None, repr=False)

    def __attrs_post_init___(self):
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


Variables = tuple[Variable, ...]


@dataclass
class Struct(Iterable[Variable]):
    name: str
    fields: Variables
    cstruct: CStruct = dfield(init=False)

    def __attrs_post_init__(self):
        c_fmt = "".join(ctype.format_character() for ctype in self.fields)
        self.cstruct = CStruct(c_fmt)

    def __iter__(self):
        yield from self.fields

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
        table = create_table(
            f"{filepath.name} - {self.size * data_len} bytes",
            columns=iter(field.name for field in self),
        )
        with filepath.open("rb") as dat:
            while d := dat.read(self.size):
                written = self.cstruct.unpack(d)
                table.add_row(*[str(d) for d in written])
        console.log(table, justify="center")

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
            "string",
            f"{self.name.lower()}ToString",
            params=[f"{self.name} {name}"],
            vret=ret,
        )

    def from_str(self) -> str:
        body: list[str] = [f"{self.name} x" + "{}"]
        for i, field in enumerate(self):
            token = f"std::string t{i} = getTokenAt(s, '-', {i})"
            body.append(token)
            if fn := field.str_to_type():
                body.append(
                    fn + f"(x.{field.name}, t{i}.c_str())"
                    if fn == "strcpy"
                    else f"x.{field.name} = {fn}(t{i})"
                )
        return build_cfn(
            self.name,
            f"{self.name.lower()}FromString",
            params=["std::string s"],
            body=body,
            vret="x",
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
            "string",
            f"{self.name.lower()}ToDebug",
            params=[f"{self.name} {name}"],
            body=body,
            vret="sout.str()",
        )

    def init(self) -> str:
        vnames = sample(ascii_lowercase[13:], k=len(self.fields))
        params = [
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
            self.name, f"new{self.name}", params=params, body=body, vret="x"
        )

    def __str__(self) -> str:
        fns = f"struct {self.name} " + "{\n"
        for field in self:
            fns += f"  {field.type} {field.name}" + (
                f"[{field.ctype}];\n" if field.ctype else ";\n"
            )
        fns += "};\n"
        return fns


Structs = list[Struct]
