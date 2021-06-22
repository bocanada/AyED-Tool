from __future__ import annotations

from pathlib import Path
from typing import Iterable

from attr import dataclass

from ayed.classes import Struct
from ayed.types import Structs
from ayed.utils import add_includes, console


@dataclass
class Printer:
    """Printer prints out an iterable of structs to either a str or a file."""

    structs: Iterable[Struct]

    def to_str(self) -> str:
        """Writes all the structs and functions to a str and returns it"""
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
            fh.write(fns)
        console.log(f"[b]Output file: {path.absolute()}[/b]", justify='center')

    @classmethod
    def from_tokens(cls, tokens: Structs) -> Printer:
        return cls(iter(tokens))
