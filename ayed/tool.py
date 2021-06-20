#!/usr/bin/env python
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from re import compile as rcompile

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(
    os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__)))
)
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
from typing import Any

from ayed.classes import Struct, Variable
from ayed.excel import Excel, write_many
from ayed.utils import (
    NoStructException,
    PromptPath,
    add_includes,
    console,
    prompt,
    edit,
)
from rich.prompt import Confirm

nfields = rcompile(
    r'struct (?P<struct>\w+)\s*{|\s*'  # struct name
    r'(?P<type>[char|signed char|unsigned char|short|short int|signed short|signed short int|unsigned short'  # data types
    r'|unsigned short int|int|signed|signed int|unsigned|unsigned int|long|long int|signed long|signed long int|unsigned long|unsigned long int'
    r'|long long|long long int|signed long long|signed long long int|unsigned long long|unsigned long long int|float|double|long double|\w]+)\s'
    r'(?P<identifier>\w+)(?P<cstr>\[\d*\])?;\s*?|(?P<ENDLINE>};)*'  # variable name | char array | };
)
char_array = rcompile(r'\[(\d*)\]')


@dataclass
class Tokenizer:
    """Struct tokenizer"""
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
        """Writes all the structs and functions to output_files/path"""
        fns = self.to_str()
        out = Path('output_files')
        out.mkdir(exist_ok=True)
        path = out / path
        with path.open('w', encoding='utf-8') as fh:
            print(fns, file=fh)
        console.log(f"[b]Wrote {path.absolute()}[/b]", justify='center')

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
            is_ctype = char_array.match(ctype.strip())
            ctype = int(is_ctype[1]) if is_ctype else 0
            struct['fields'].append(Variable(ttype.strip(), vname.strip(), ctype))
        if not struct['name']:
            raise NoStructException(
                "Couldn't find a struct to parse. Make sure the struct is well formatted."
            )
        return tokens

    @classmethod
    def from_str(cls, code: str) -> 'Tokenizer':
        tokens = cls.__build(code)
        return cls(tokens)

    @classmethod
    def from_path(cls, path: Path) -> 'Tokenizer':
        with path.open() as fh:
            tokens = cls.__build(fh.read())
        return cls(tokens)


def main():
    console.print(
        "1. [b white]Coll fn generator[/b white]\n2. [b white]Files generator[/b white]",
    )
    option = prompt.ask(
        console=console,
        prompt="[b]Option",
        choices=['1', '2'],
        show_choices=True,
    )
    if option == "1":
        if Confirm.ask("[b]Open editor?", default='y'):
            SEPARATOR = '// write your code below'
            code = edit(SEPARATOR)
            t = Tokenizer.from_str(code)
        else:
            path = PromptPath.ask("Enter path to a .cpp[,.hpp,.c,.h]", console=console)
            t = Tokenizer.from_path(path)
        dt = datetime.now().strftime("%d-%m-%y-%H%M")
        t.to_file(Path(f'{dt}.hpp'))
        structs = ', '.join(struct.name for struct in t.structs)
        console.print(
            f"[b yellow]Wrote TtoDebug, TtoString, TfromString and newT for {structs}",
            justify='center',
        )
    else:
        path = PromptPath.ask(
            "[b]Enter path to a .xlsx[/b] 👀",
            console=console,
            default="AlgoritmosFiles.xlsx",
            show_default=True,
        )
        if Confirm.ask(
            "Por default, esto abrirá el excel y escribirá archivos en [i]output_files/[/i]. Continuar?",
            default="y",
        ):
            excel = Excel(path)
            excel.read()
            f = excel.read_sheets()
            write_many(f)
    console.print("[b white]Done! Bye! 👋", justify='center')


if __name__ == "__main__":
    main()
