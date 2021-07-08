from __future__ import annotations

from pathlib import Path
from typing import Iterator, Union

from attr import dataclass
from pandas import DataFrame, Series

from ayed.classes import Struct, Variable

PathLike = Union[Path, str]
PandasDF = Union[DataFrame, dict[str, DataFrame]]
Sheet = Union[DataFrame, Series]
Variables = list[Variable]


@dataclass(slots=True)
class File:
    """
    Represents the structure of an excel sheet. Ex:
    filenames: [VUELOS.dat, ...]
    structs: [Vuelo]
    variables: [struct variables to be written to a file]
    """

    filenames: list[str]
    structs: list[str]
    variables: Variables

    def __iter__(self) -> Iterator[tuple[str, Struct]]:
        for i, fname in enumerate(self.filenames):
            vars: list[Variable] = []
            for var in self.variables:
                if var.struct_id == i:
                    vars.append(var)
                    continue
            yield fname, Struct(name=self.structs[i], fields=vars)


Files = list[dict[str, File]]
Structs = list[Struct]
