from copy import deepcopy
from io import TextIOWrapper
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from pprint import pprint
from unicodedata import category, normalize

from pandas import DataFrame, Series, isna, read_excel

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(
    os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__)))
)
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
from re import compile
from typing import Optional, Union

from ayed.classes import C_DTYPES, File, Struct, Variable, cfunc

char_array = compile(r'char(\[\d*\])')

PathLike = Union[Path, str]
PandasDF = Union[DataFrame, dict[str, DataFrame]]
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

    def read(self):
        self.df = read_excel(self.file_path.absolute().as_uri(), sheet_name=self.sheet)  # type: ignore

    def read_sheets(self) -> FILES:
        files = []
        if not isinstance(self.df, dict) or not self.df:
            raise TypeError(
                f'Expected {dict[str, DataFrame]} but got {type(self.df)}. Try using read_sheet instead.'
            )
        for sheet_name, data in self.df.items():
            print(f"Reading... {sheet_name}")
            data = data.dropna(axis='columns', how='all')
            file = File(filenames=[], structs=[], variables=[])
            self.read_sheet(file=file, inplace=True, df=data)
            files.append({sanitize_name(sheet_name): file})
            assert len(file['filenames']) == len(file['structs'])
            print(f'Found {len(file["structs"])} structs')
        return files

    def read_sheet(
        self,
        *,
        df: Optional[DataFrame] = None,
        file: Optional[File] = None,
        inplace: Optional[bool] = False,
    ) -> File:
        if not df:
            df = self.df
        df = df.dropna(axis='columns', how='all')
        file = (
            File(filenames=[], structs=[], variables=[])
            if not file
            else file
            if not inplace
            else deepcopy(file)
        )
        if not isinstance(self.df, DataFrame):
            raise TypeError(
                f'Expected {DataFrame}|{Series} but got {type(self.df)}. Try using read_sheets instead.'
            )
        for (_, content) in df.iteritems():
            if content.empty:
                continue
            var = Variable(
                file_id=0, struct_id=0, type='', name='', ctype=None, data=[]
            )
            for (_, item) in content.items():
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
                        var.ctype = c[1] if c else None
                        continue
                var.struct_id = len(file['structs']) - 1
                var.file_id = len(file['filenames']) - 1
                var.data.append(item)
            file['variables'].append(var)
        return file


def add_includes(*, libs: list[str]) -> str:
    lib = ["#include " f'<{lib}>' if not "/" in lib else f'"{lib}"' for lib in libs]
    return '\n'.join(lib)


def writer_from_file(file: File, *, sheet_name: str) -> None:
    sheet_name = sanitize_name(sheet_name)
    with open(f'{sheet_name}.cpp', 'w') as fh:
        print(
            add_includes(
                libs=[
                    'filesystem',
                    'cstdio',
                    'iostream',
                    'cstring',
                    'string',
                    'biblioteca/funciones/tokens.hpp',
                ],
            )
        )
        for i, fname in enumerate(file['filenames']):
            vars: list[Variable] = []
            for var in f['variables']:
                if var.struct_id == i:
                    vars.append(var)
                    continue
            s = Struct(name=file['structs'][i], fields=tuple(vars))
            print(s, file=fh)
            print(s.to_debug(), file=fh)
            print(s.writer(sheet_name, fname), file=fh)
        fn_body = [
            f'std::cout << "--" << "{f}" << "--" << std::endl;\n  write{f.split(".")[0]}()'
            for f in f['filenames']
        ]
        print(cfunc('int', 'main', body=fn_body, vret="0"), file=fh)


def writers_from_file(files: FILES) -> None:
    if not isinstance(files, list):
        raise ValueError(
            f'Expected {list} of {dict} but got {type(files)}. Try using struct_from_file instead.'
        )
    for file in files:
        for (sheet_name, f) in file.items():
            writer_from_file(f, sheet_name=sheet_name)


if __name__ == "__main__":
    excel = Excel('./ayed/AlgoritmosFiles.xlsx', sheet="Compañía de aviación")
    excel.read()
    f = excel.read_sheet()
    pprint(f)
    writer_from_file(f, sheet_name=excel.sheet)
