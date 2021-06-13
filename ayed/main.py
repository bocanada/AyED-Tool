#!/usr/bin/env python
from dataclasses import dataclass
from re import compile
from pathlib import Path
import sys
import os

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(
    os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__)))
)
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
from ayed.classes import Struct, Variable
from typing import Any, Iterable

struct_name = compile(r"^struct\s+(?P<name>\w+)\s*{$")
fields = compile(r"^(?P<type>[\w\s]*)\s+(?P<identifier>\w+)(?P<cstr>\[\d*\])?")


@dataclass
class Tokenizer:
    tokens: list[Struct]

    def to_str(self) -> str:
        s = ""
        for token in self.tokens:
            s += str(token.from_str())
            s += str(token.to_str())
            s += str(token.init())
        return s

    def to_file(self, path: Path) -> None:
        with path.open('w', encoding='utf-8') as fh:
            for token in self.tokens:
                print(token, file=fh)

    @staticmethod
    def __build(lines: Iterable[str]) -> list[Struct]:
        tokens: list[Struct] = []
        struct: dict[str, Any] = {'name': '', 'fields': []}
        for i in lines:
            line = i.strip()
            if line == '};':
                tokens.append(Struct(**struct))
                struct['name'] = None
                struct['fields'] = []
            if not line:
                continue
            if v := struct_name.match(line):
                struct['name'] = v.groupdict()['name']
                continue
            field = fields.match(line)
            if field is not None:
                dtype, vname, ctype = field.group('type', 'identifier', 'cstr')
                struct['fields'].append(Variable(dtype, vname, ctype))  # type: ignore
        return tokens

    @classmethod
    def from_str(cls, code: str) -> 'Tokenizer':
        tokens = cls.__build(code.splitlines())
        return cls(tokens)

    @classmethod
    def from_path(cls, path: Path) -> 'Tokenizer':
        tokens = cls.__build(path.open())
        return cls(tokens)


if __name__ == "__main__":
    path = Path('/home/wipedout/Development/ayed/tests/structs/structs.cpp')
    tokens = Tokenizer.from_path(path)
    print(str(tokens.tokens[0]))
    # tokens.to_file(Path('./asd.hpp'))
