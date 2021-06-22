from __future__ import annotations

from pathlib import Path
from re import compile as rcompile
from typing import Any, Pattern

from ayed.classes import Struct, Variable
from ayed.types import Structs
from ayed.utils import NoStructException


class Tokenizer:
    """Struct tokenizer"""

    nfields: Pattern = rcompile(
        r'struct (?P<struct>\w+)\s*{|\s*'  # struct name
        r'(?P<type>[char|signed char|unsigned char|short|short int|signed short|signed'
        r'short int|unsigned short|unsigned short int|int|signed|signed int|unsigned|'
        r'unsigned int|long|long int|signed long|signed long int|unsigned long|unsigned'
        r' long int|long long|long long int|signed long long|signed long long int|'
        r'unsigned long long|unsigned long long int|float|double|long double|\w]+)\s'
        r'(?P<identifier>\w+)(?P<cstr>\[\d*\])?;\s*?|(?P<ENDLINE>};)*'
    )
    char_array: Pattern = rcompile(r'\[(\d*)\]')

    @staticmethod
    def __build(lines: str) -> Structs:
        tokens: Structs = []
        struct: dict[str, Any] = {'name': '', 'fields': []}
        fields: list[tuple[str, str, str, str, str]] = Tokenizer.nfields.findall(lines)
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
            is_ctype = Tokenizer.char_array.match(ctype.strip())
            ctype = int(is_ctype[1]) if is_ctype else 0
            struct['fields'].append(Variable(ttype.strip(), vname.strip(), ctype=ctype))
        if not struct['name']:
            raise NoStructException(
                "Couldn't find a struct to parse."
                " Make sure the struct is well formatted."
            )
        return tokens

    @classmethod
    def from_str(cls, code: str) -> Structs:
        tokens = cls.__build(code)
        return tokens

    @classmethod
    def from_path(cls, path: Path) -> Structs:
        with path.open() as fh:
            tokens = cls.__build(fh.read())
        return tokens
