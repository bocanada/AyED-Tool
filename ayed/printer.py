from pathlib import Path
from typing import Iterable

from attr import dataclass

from ayed.classes import Struct, Structs
from ayed.utils import add_includes, console


@dataclass
class Printer:
    structs: Iterable[Struct]

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
            fh.write(fns)
        console.log(f"[b]Wrote {path.absolute()}[/b]", justify='center')

    @classmethod
    def from_tokens(cls, tokens: Structs):
        return cls(iter(tokens))