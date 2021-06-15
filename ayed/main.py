#!/usr/bin/env python
from dataclasses import dataclass
from re import compile
from pathlib import Path
import sys
import os
from datetime import datetime

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(
    os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__)))
)
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
from ayed.classes import Struct, Variable
from ayed.excel import add_includes
from typing import Any

nfields = compile(
    r'struct (?P<struct>\w+)\s{|\s*'  # struct name
    r'(?P<type>[char|signed char|unsigned char|short|short int|signed short|signed short int|unsigned short'  # data types
    r'|unsigned short int|int|signed|signed int|unsigned|unsigned int|long|long int|signed long|signed long int|unsigned long|unsigned long int'
    r'|long long|long long int|signed long long|signed long long int|unsigned long long|unsigned long long int|float|double|long double|\w]+)\s'
    r'(?P<identifier>\w+)(?P<cstr>\[\d*\])?;\s*?|(?P<ENDLINE>};)*'  # variable name | char array | };
)


@dataclass
class Tokenizer:
    structs: list[Struct]

    def to_str(self) -> str:
        s = add_includes(
            libs=[
                'filesystem',
                'cstdio',
                'iostream',
                'cstring',
                'string',
                'biblioteca/funciones/tokens.hpp',
            ],
        )
        for token in self.structs:
            s += str(token)
            s += token.init()
            s += token.to_str()
            s += token.from_str()
            s += token.to_debug()
        return s

    def to_file(self, path: Path) -> None:
        with path.open('w', encoding='utf-8') as fh:
            fns = self.to_str()
            print(fns, file=fh)

    @staticmethod
    def __build(lines: str) -> list[Struct]:
        tokens: list[Struct] = []
        struct: dict[str, Any] = {'name': '', 'fields': []}
        fields: list[tuple[str, str, str, str, str]] = nfields.findall(lines)
        for (sname, ttype, vname, ctype, endl) in fields:
            if endl:
                tokens.append(Struct(**struct))
                struct['fields'] = []
                continue
            if not any([sname, ttype, vname, ctype]):
                continue
            if sname:
                struct['name'] = sname.strip()
                continue
            struct['fields'].append(Variable(ttype.strip(), vname.strip(), ctype))
        return tokens

    @classmethod
    def from_str(cls, code: str) -> 'Tokenizer':
        tokens = cls.__build(code)
        return cls(tokens)

    @classmethod
    def from_path(cls, path: Path) -> 'Tokenizer':
        tokens = cls.__build(path.open().read())
        return cls(tokens)


if __name__ == "__main__":
    dt = datetime.now().strftime("%d-%m-%y")
    path = Path(input()).absolute()
    if not path.exists():
        raise SystemExit('Error: El archivo no existe.')
    tokens = Tokenizer.from_path(path)
    tokens.to_file(Path(f'./{dt}.hpp'))
