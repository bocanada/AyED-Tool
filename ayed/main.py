#!/usr/bin/env python
from dataclasses import dataclass
from re import compile
from pathlib import Path
import sys
import os

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
from ayed.classes import Struct
from typing import Any

struct_name = compile(r"^struct\s+(?P<name>\w+)\s*{$")
fields = compile(r"^(?P<type>[\w\s]*)\s+(?P<identifier>\w+)(?P<cstr>\[\d*\])?")


@dataclass
class Tokenizer:
    tokens: list[Struct]

    def to_file(self, path: Path) -> None:
        with path.open('w', encoding='utf-8') as fh:
            for token in self.tokens:
                print(token.from_str(), file=fh)
                print(token.to_str('-'), file=fh)
                print(token.init(), file=fh)

    @classmethod
    def from_path(cls, path: Path) -> 'Tokenizer':
        tokens: list[Struct] = []
        struct: dict[str, Any] = {'name': '', 'fields': []}

        for i in path.open():
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
        return cls(tokens)


if __name__ == "__main__":
    path = Path('/home/wipedout/Development/ayed/ayed/structs.cpp')
    print(path.absolute())
    tokens = Tokenizer.from_path(path)
    tokens.to_file(Path('./asd.hpp'))
