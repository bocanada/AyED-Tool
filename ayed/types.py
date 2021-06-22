from __future__ import annotations

from pathlib import Path
from typing import TypedDict, Union

from pandas import DataFrame, Series

from ayed.classes import Struct, Variable

PathLike = Union[Path, str]
PandasDF = Union[DataFrame, dict[str, DataFrame]]
Sheet = Union[DataFrame, Series]
Variables = list[Variable]


class File(TypedDict):
    """
    Represents the structure of an excel sheet. Ex:
    filenames: [VUELOS.dat, ...]
    structs: [Vuelo]
    variables: [struct variables to be written to a file]
    """

    filenames: list[str]
    structs: list[str]
    variables: Variables


Files = list[dict[str, File]]
Structs = list[Struct]
