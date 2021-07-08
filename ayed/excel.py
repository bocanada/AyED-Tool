from __future__ import annotations

from pathlib import Path

import attr
from pandas import DataFrame, Series, isna, read_excel
from regex import compile

from ayed.classes import C_DTYPES, Variable
from ayed.types import File, Files, PandasDF, PathLike, Sheet
from ayed.utils import console, sanitize_name

char_array = compile(r"char\[(\d*)\]")


@attr.s(slots=True)
class Excel:
    file_path: PathLike = attr.ib()
    sheet: str | None = attr.ib(default=None)
    df: PandasDF | None = attr.ib(default=None, init=False, repr=False)

    def __attrs_post_init__(self) -> None:
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)
        self.df = read_excel(self.file_path.absolute().as_uri(), sheet_name=self.sheet)

    def read(self) -> File | Files:
        if self.sheet is None:
            return self.__read_sheets()
        return self.__read_sheet()

    def __read_sheets(self) -> Files:
        files = []
        if not (isinstance(self.df, dict) or self.df):
            raise AssertionError('Maybe you meant to use "read_sheet".')
        with console.status("Parsing structs..."):
            for sheet_name, data in self.df.items():
                data = data.dropna(axis="columns", how="all")
                file = File(filenames=[], structs=[], variables=[])
                self.__read_sheet(file=file, df=data)
                files.append({sanitize_name(sheet_name): file})  # type: ignore
                if len(file.filenames) != len(file.structs):
                    raise AssertionError(
                        f"{len(file.filenames)=} != {len(file.structs)=}"
                    )
                console.log(
                    f"Found {len(file.structs)} structs in {sheet_name} 🙉",
                    justify="center",
                )
            return files

    def __read_sheet(
        self,
        *,
        df: Sheet | None = None,
        file: File | None = None,
    ) -> File:
        if df is None:
            df = self.df  # type: ignore
        if not isinstance(df, (DataFrame, Series)):
            raise ValueError("You should probably use read_sheets")
        df = df.dropna(axis="columns", how="all")
        if not file:
            file = File(filenames=[], structs=[], variables=[])
        for (_, content) in df.items():
            if content.empty:
                continue
            var = Variable(type="", name="", ctype=None)
            for item in content.values:
                if isna(item):
                    continue
                if isinstance(item, str):
                    item = item.strip()  # sometimes items have spaces and such
                    if item.startswith("struct"):
                        _, struct = item.split()
                        file.structs.append(struct)
                        continue
                    if item.endswith(".dat"):
                        file.filenames.append(item)
                        continue
                    if var.type and not var.name:
                        var.name = item
                        continue
                    if (c := char_array.match(item)) or item in C_DTYPES:
                        var.type = item.split("[")[0]
                        var.ctype = int(c[1]) if c else None
                        continue
                var.struct_id = len(file.structs) - 1
                var.file_id = len(file.filenames) - 1
                var.data.append(
                    item if not var.ctype else item.ljust(var.ctype).encode("utf-8")
                )
            file.variables.append(var)
        return file
