from string import ascii_lowercase
from typing import NamedTuple, Optional
from dataclasses import dataclass, field
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


@dataclass
class CFunc:
    ret: str
    name: str
    params: list[str]
    vret: str
    body: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f'{self.ret} {self.name}({", ".join(self.params)})\n'
            + '{\n'
            + (';\n'.join(self.body) + ';\n' if self.body else '')
            + f'return {self.vret};'
            + '\n'
            + '};\n'
        )


@dataclass
class Struct:
    name: str
    fields: tuple[Variable, ...]

    def to_str(self, sep: str) -> CFunc:
        name = self.name[0].lower()
        variables: list[str] = []
        for var in self.fields:
            if var.type == 'string':
                variables.append(var.name)
                continue
            s = f'{var.type_to_str()}({name}.{var.name})'
            variables.append(s)
        ret = f"+'{sep}'+".join(variables)
        return CFunc(
            'string', f'{self.name.lower()}ToString', [f'{self.name} {name}'], ret
        )

    def from_str(self) -> CFunc:
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
        func = CFunc(
            self.name,
            f'{self.name.lower()}FromString',
            [f'string {name}'],
            'x',
            variables,
        )
        return func

    def init(self) -> CFunc:
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
        return CFunc(self.name, f'new{self.name}', parameters, 'x', body=body)
