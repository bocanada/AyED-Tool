from string import ascii_lowercase
from typing import NamedTuple, Optional
from dataclasses import dataclass
from random import sample

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


class Variable(NamedTuple):
    type: str
    name: str
    ctype: Optional[str]

    def type_to_str(self) -> str:
        return (
            f'{self.type.lower()}ToString'
            if not self.type in C_DTYPES
            else ''  # if type not in C_DTYPES, either return '' or tToString
            if self.type == 'char'
            else 'to_string'
        )

    def str_to_type(self) -> str:
        if self.ctype:
            return 'strcpy'
        return {'int': 'stoi'}.get(self.type, f'{self.type.lower()}FromString')


def cfunc(
    ret: str,
    name: str,
    vret: str,
    *,
    params: Optional[list[str]],
    body: Optional[list[str]] = None,
) -> str:
    """Builds a C function"""
    if body:
        body = ["  " + line for line in body]
    return (
        f'{ret} {name}({", ".join(params or [])})\n'  # returntype functionName(type varname, for all params)
        + '{\n'  # {
        + (';\n'.join(body) + ';\n' if body else '')  # function body
        + f'  return {vret};'  # return varname;
        + '\n'
        + '};\n'  # };
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
            'string',
            f'{self.name.lower()}ToString',
            ret,
            params=[f'{self.name} {name}'],
        )

    def from_str(self) -> str:
        name = self.name[0].lower()
        variables: list[str] = [f'{self.name} x']
        for i, var in enumerate(self.fields):
            token = f"string t{i} = getTokenAt({name}, '-', {i})"
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
            'x',
            params=[f'string {name}'],
            body=variables,
        )

    def init(self) -> str:
        vnames = sample(ascii_lowercase[13:], k=len(self.fields))
        parameters = [
            f'{field.type if not field.ctype else "string"} {vnames[i]}'
            for i, field in enumerate(self.fields)
        ]
        body: list[str] = [f'{self.name} x']
        for i, var in enumerate(self.fields):
            if var.ctype:
                body.append(f'{var.str_to_type()}(x.{var.name}, {vnames[i]}.c_str())')
                continue
            line = f"x.{var.name} = {vnames[i]}"
            body.append(line)
        return cfunc(self.name, f'new{self.name}', 'x', params=parameters, body=body)

    def __str__(self) -> str:
        fns = ""
        fns += self.init()
        fns += self.to_str('-')
        fns += self.from_str()
        return fns
