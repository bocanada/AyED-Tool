from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union
from unicodedata import category, normalize

from pandas import DataFrame, Series, isna, read_excel
from regex import compile

from ayed.classes import C_DTYPES, File, Struct, Variable
from ayed.utils import console

char_array = compile(r'char\[(\d*)\]')

PathLike = Union[Path, str]
PandasDF = Union[DataFrame, dict[str, DataFrame]]
Sheet = Union[DataFrame, Series]
FILES = list[dict[str, File]]


def sanitize_name(fname: str) -> str:
    return ''.join(
        c for c in normalize('NFD', fname) if category(c) != 'Mn' and c != ' '
    )


@dataclass
class Excel:
    file_path: PathLike
    sheet: Optional[str] = field(default=None)
    df: Optional[PandasDF] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)

    def read(self, *, sheet: Optional[str] = None):
        if sheet:
            self.sheet = sheet
        self.df = read_excel(self.file_path.absolute().as_uri(), sheet_name=self.sheet)  # type: ignore

    def read_sheets(self) -> FILES:
        files = []
        assert (
            isinstance(self.df, dict) or self.df
        ), 'Maybe you meant to use "read_sheet".'
        with console.status("Parsing structs...") as _:
            for sheet_name, data in self.df.items():
                data = data.dropna(axis='columns', how='all')
                file = File(filenames=[], structs=[], variables=[])
                self.read_sheet(file=file, df=data)
                files.append({sanitize_name(sheet_name): file})  # type: ignore
                assert len(file['filenames']) == len(file['structs'])
                console.log(f'Found {len(file["structs"])} structs 🙉', justify='center')
            return files

    def read_sheet(
        self,
        *,
        df: Optional[Sheet] = None,
        file: Optional[File] = None,
    ) -> File:
        if df is None:
            df = self.df  # type: ignore
        assert isinstance(
            df, (DataFrame, Series)
        ), "You should probably use read_sheets"
        df = df.dropna(axis='columns', how='all')
        if not file:
            file = File(filenames=[], structs=[], variables=[])
        for (_, content) in df.iteritems():
            if content.empty:
                continue
            var = Variable(
                file_id=0, struct_id=0, type='', name='', ctype=None, data=[]
            )
            for item in content.values:
                if isna(item):
                    continue
                if isinstance(item, str):
                    item = item.strip()  # sometimes items have spaces and such
                    if item.startswith('struct'):
                        _, struct = item.split()
                        file['structs'].append(struct)
                        continue
                    if item.endswith('.dat'):
                        file['filenames'].append(item)
                        continue
                    if var.type and not var.name:
                        var.name = item
                        continue
                    if (c := char_array.match(item)) or item in C_DTYPES:
                        var.type = item.split('[')[0]
                        var.ctype = int(c[1]) if c else None
                        continue
                var.struct_id = len(file['structs']) - 1
                var.file_id = len(file['filenames']) - 1
                var.data.append(
                    item if not var.ctype else item.ljust(var.ctype).encode('utf-8')
                )
            file['variables'].append(var)
        return file


def write_one(file: File, *, sheet_name: str, unpack: Optional[bool] = True) -> None:
    assert sheet_name is not None
    sheet_name = sanitize_name(sheet_name)
    for i, fname in enumerate(file['filenames']):
        vars: list[Variable] = []
        for var in file['variables']:
            if var.struct_id == i:
                vars.append(var)
                continue
        s = Struct(name=file['structs'][i], fields=tuple(vars))
        s.pack(fname, unpack=unpack)  # packs the struct into output_files/fname


def write_many(files: FILES, *, unpack: Optional[bool] = True) -> None:
    if not isinstance(files, list):
        raise ValueError(
            f'Expected {list} of {dict} but got {type(files)}. Try using struct_from_file instead.'
        )
    for file in files:
        for (sheet_name, fh) in file.items():
            write_one(fh, sheet_name=sheet_name, unpack=unpack)
