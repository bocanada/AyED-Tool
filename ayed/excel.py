from pandas import DataFrame, read_excel, isna
from classes import Variable, C_DTYPES, File
from copy import deepcopy
from typing import Optional
from re import compile

char_array = compile(r'char(\[\d*\])')

excel = read_excel('./ayed/AlgoritmosFiles.xlsx', sheet_name=None)


def read_sheet(df: DataFrame, file: File, *, inplace: Optional[bool] = True) -> File:
    if not inplace:
        file = deepcopy(file)
    for (_, content) in df.iteritems():
        if content.empty:
            continue
        var = Variable(file_id=0, struct_id=0, type='', name='', ctype=None, data=[])
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


def read_sheets(excel: dict[str, DataFrame]) -> list[File]:
    files = []
    for sheet_name, data in excel.items():
        print(f"Reading... {sheet_name}")
        data = data.dropna(axis='columns', how='all')
        file = File(filenames=[], structs=[], variables=[])
        read_sheet(data, file)
        files.append(file)
        assert len(file['filenames']) == len(file['structs'])
        print(f'Found {len(file["structs"])} structs')
    return files