from string import ascii_lowercase
from typing import Any, Optional, TypedDict
from dataclasses import dataclass, field
from random import sample

ascii_lowercase = ''.join(x for x in ascii_lowercase if x != 'x')

C_DTYPES = {
    'char',
    'signed char',
    'unsigned char',
    'short',
    'short int',
    'signed short',
    'signed short int',
    'unsigned short',
    'unsigned short int',
    'int',
    'signed',
    'signed int',
    'unsigned',
    'unsigned int',
    'long',
    'long int',
    'signed long',
    'signed long int',
    'unsigned long',
    'unsigned long int',
    'long long',
    'long long int',
    'signed long long',
    'signed long long int',
    'unsigned long long',
    'unsigned long long int',
    'float',
    'double',
    'long double',
}


@dataclass
class Variable:
    type: str
    name: str
    ctype: Optional[str] = None
    data: list[Any] = field(
        default_factory=list
    )  # the data that the variable holds. Used when loading an excel file
    struct_id: Optional[int] = None
    file_id: Optional[int] = None

    def __post_init__(self):
        if self.type == 'string':
            self.type = 'std::string'

    def type_to_str(self) -> str:
        return (
            f'{self.type.lower()}ToString'
            if not self.type in C_DTYPES
            else ''  # if type not in C_DTYPES, either return '' or tToString
            if self.type == 'char'
            else 'std::to_string'
        )

    def str_to_type(self) -> str:
        if self.ctype:
            return 'strcpy'
        return {'int': 'stoi'}.get(self.type, f'{self.type.lower()}FromString')


class File(TypedDict):
    filenames: list[str]
    structs: list[str]
    variables: list[Variable]


def cfunc(
    ret: str,
    name: str,
    *,
    params: Optional[list[str]] = None,
    body: Optional[list[str]] = None,
    vret: Optional[str] = None,
) -> str:
    """Builds a C function"""
    if body:
        body = ["  " + line for line in body]
    return (
        f'{ret} {name}({", ".join(params or [])})\n'  # returntype functionName(type varname, for all params)
        + '{\n'  # {
        + (';\n'.join(body) + ';\n' if body else '')  # function body
        + (f'  return {vret};\n' if ret != 'void' else '')
        + '};\n'  # return varname;  # };
    )


@dataclass
class Struct:
    name: str
    fields: tuple[Variable, ...]

    def to_str(self, sep: Optional[str] = '-') -> str:
        name = self.name[0].lower()
        variables: list[str] = []
        for var in self.fields:
            if var.type == 'string':
                variables.append(var.name)
                continue
            s = f'{var.type_to_str()}({name}.{var.name})'
            variables.append(s)
        ret = f"+'{sep}'+".join(variables)
        return cfunc(
            'std::string',
            f'{self.name.lower()}ToString',
            vret=ret,
            params=[f'{self.name} {name}'],
        )

    def writer(self, folder_name: str, file_name: str) -> str:
        fname = file_name.split('.')[0]
        fname = f'write{fname}'
        body = [
            f'std::filesystem::create_directory("{folder_name}")',
            f'FILE* f = fopen("{folder_name}/{file_name}", "w+b")',
            f'{self.name} x' + "{}",
        ]
        size = len(self.fields[0].data)
        for i in range(size):
            for field in self.fields:
                if field.type == 'string':
                    field.type = 'std::string'
                if field.ctype:
                    body.append(
                        f'{field.str_to_type()}(x.{field.name}, "{field.data[i]}")'
                    )
                    continue
                assign = (
                    f'{field.data[i]}' if field.type != 'char' else f"'{field.data[i]}'"
                )
                body.append(f'x.{field.name} = {assign}')
            body.append(f'fwrite(&x, sizeof({self.name}), 1, f)')
        body.append('fclose(f)')
        fn = cfunc('void', fname, vret=None, body=body)
        return fn

    def from_str(self) -> str:
        name = self.name[0].lower()
        variables: list[str] = [f'{self.name} x' + "{}"]
        for i, var in enumerate(self.fields):
            token = f"std::string t{i} = getTokenAt({name}, '-', {i})"
            variables.append(token)
            if fn := var.str_to_type():
                variables.append(
                    fn + f'(x.{var.name}, t{i}.c_str())'
                    if fn == 'strcpy'
                    else f'x.{var.name} = {fn}(t{i})'
                )
        return cfunc(
            self.name,
            f'{self.name.lower()}FromString',
            vret='x',
            params=[f'std::string {name}'],
            body=variables,
        )

    def to_debug(self) -> str:
        name = self.name.lower()[0]
        body = ["std::stringstream sout", f'sout << "{self.name}"' + ' << "{"']
        for i, field in enumerate(self.fields):
            body.append(
                f'sout << "{field.name} : " << {name}.{field.name} '
                + ('<< ", "' if i != len(self.fields) -1 else '')
            )
        body.append('sout << "};"')
        return cfunc(
            'std::string',
            f'{self.name.lower()}ToDebug',
            params=[f'{self.name} {name}'],
            body=body,
            vret="sout.str()",
        )

    def init(self) -> str:
        vnames = sample(ascii_lowercase[13:], k=len(self.fields))
        parameters = [
            f'{field.type if not field.ctype else "std::string"} {vnames[i]}'
            for i, field in enumerate(self.fields)
        ]
        body: list[str] = [f'{self.name} x' + "{}"]
        for i, var in enumerate(self.fields):
            if var.ctype:
                body.append(f'{var.str_to_type()}(x.{var.name}, {vnames[i]}.c_str())')
                continue
            line = f"x.{var.name} = {vnames[i]}"
            body.append(line)
        return cfunc(
            self.name, f'new{self.name}', vret='x', params=parameters, body=body
        )

    def __str__(self) -> str:
        fns = f"struct {self.name} " + "{\n"
        for field in self.fields:
            fns += f"  {field.type} {field.name}" + (
                f'{field.ctype};\n' if field.ctype else ';\n'
            )
        fns += "};\n"
        fns += self.init()
        fns += self.to_str('-')
        fns += self.from_str()
        return fns
