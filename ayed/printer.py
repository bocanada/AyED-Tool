from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from attr import dataclass, field

from ayed.classes import Struct
from ayed.excel import Excel
from ayed.types import File, Files, Structs
from ayed.utils import add_includes, console, sanitize_name


class Printer(ABC):
    @abstractmethod
    def to_str(self):
        return NotImplemented

    @abstractmethod
    def to_file(self):
        return NotImplemented


@dataclass
class StructPrinter(Printer):
    """Printer prints out an iterable of structs to either a str or a file."""

    structs: Iterable[Struct]

    def to_str(self) -> str:
        """Writes all the structs and functions to a str and returns it"""
        s = add_includes(
            libs=[
                "filesystem",
                "cstdio",
                "iostream",
                "cstring",
                "string",
                "biblioteca/funciones/tokens.hpp",
            ],
        )
        fbody = [
            f"{str(token)}{token.init()}{token.to_str()}{token.from_str()}{token.to_debug()}"
            for token in self.structs
        ]
        return s + "\n".join(fbody)

    def to_file(self, path: Path) -> None:
        """Writes all the structs and functions to output_files/path"""
        fns = self.to_str()
        out = Path("output_files")
        out.mkdir(exist_ok=True)
        path = out / path
        with path.open("w", encoding="utf-8") as fh:
            fh.write(fns)
        console.log(
            f"[b]Output file: [magenta]{path.absolute().as_uri()}[/magenta][/b]",
            justify="center",
        )

    @classmethod
    def from_tokens(cls, tokens: Structs) -> "StructPrinter":
        return cls(iter(tokens))


@dataclass(slots=True)
class ExcelPrinter(Printer):
    file: Excel
    output_folder: Path = Path("output_files")
    data: File | Files = field(init=False)

    def _write_one(
        self, *, file: File = None, sheet_name: str | None = None
    ) -> dict[str, list[list[bytes]]]:
        if not file:
            file = self.data  # type: ignore
        sheet_name = sanitize_name(sheet_name or self.file.sheet)  # type: ignore
        packed_structs = defaultdict(list)
        for fname, struct in file:
            packed = struct.pack()
            packed_structs[fname].append(packed)
        return packed_structs  # packs the struct into output_files/fname

    def _write_many(self):
        if not isinstance(self.data, list):
            raise ValueError(
                f"Expected {list} of {dict} but got {type(self.file)}."
                " Try using struct_from_file instead."
            )
        return [
            [
                self._write_one(file=fh, sheet_name=sheet_name)
                for (sheet_name, fh) in file.items()
            ]
            for file in self.data
        ]

    def _write(self, bytes: dict[str, list[list[bytes]]]):
        for fname, data in bytes.items():
            with (self.output_folder / fname).open("wb") as fh:
                for raw_bytes in data[0]:
                    fh.write(raw_bytes)

    def to_file(self):
        if not self.output_folder.exists():
            self.output_folder.mkdir(exist_ok=True)
        if isinstance(self.data, File):
            to_write = self._write_one()
            self._write(to_write)
            return True
        to_write = self._write_many()
        for bytes_list in to_write:
            for packed_structs in bytes_list:
                self._write(packed_structs)
        return True

    def to_table(self):
        if isinstance(self.data, File):
            for fname, struct in self.data:
                struct.unpack(self.output_folder / fname)
            return
        for sheet in self.data:
            for _, file in sheet.items():
                for fname, struct in file:
                    struct.unpack(self.output_folder / fname)

    def to_str(self):
        if isinstance(self.data, File):
            to_write = self._write_one()
            return "".join(f"{fname} -->\n {data}" for fname, data in to_write.items())
        raise NotImplementedError

    def __enter__(self) -> "ExcelPrinter":
        self.data = self.file.read()
        return self

    def __exit__(self, *args):
        del self.data
        return False


if __name__ == "__main__":
    e = Excel("AlgoritmosFiles.xlsx")
    with ExcelPrinter(e) as p:
        p.to_file()
