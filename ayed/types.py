from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, Union

from pandas import DataFrame, Series

from ayed.classes import Variable, Struct

PathLike = Union[Path, str]
PandasDF = Union[DataFrame, dict[str, DataFrame]]
Sheet = Union[DataFrame, Series]
Variables = list[Variable]


class File(TypedDict):
    filenames: list[str]
    structs: list[str]
    variables: Variables


Files = list[dict[str, File]]
Structs = list[Struct]


@dataclass
class ReadSheetException(Exception):
    message: str

    def __str__(self) -> str:
        return self.message
