#!/usr/bin/env python
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Final, Optional

from typer import Argument, Option, Typer

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(
    os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__)))
)
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))


from ayed.excel import Excel, write_many, write_one
from ayed.parser import Tokenizer
from ayed.printer import Printer
from ayed.types import Structs
from ayed.utils import console, edit

app = Typer(name='ayed')

DEFAULT_EXCEL: Final = "AlgoritmosFiles.xlsx"


def open_editor() -> Structs:
    SEPARATOR = '// write your code below'
    code = edit(SEPARATOR)
    return Tokenizer.from_str(code)


@app.command(name='coll')
def coll_fn_gen(
    path: Path = Option(
        None,
        "--path",
        "-p",
        exists=True,
        dir_okay=False,
        resolve_path=True,
        help="La dirección del archivo .cpp[,.hpp,.c,.h] que contiene a los structs",
    )
) -> None:
    """
    Crea las funciones newT, TToString, TFromString, TToDebug para un struct T.

    Por default, abre un editor - $VISUAL o NOTEPAD en Win,
    $EDITOR o vi/vim/nvim/nano en Linux - en el que podrán escribir sus structs.

    Si ya tienen un archivo y no quieren que se abra el editor, pueden usar
    -p o --path [PATH], siendo [PATH] el nombre del archivo
    """
    if not path:
        structs = open_editor()
    else:
        structs = Tokenizer.from_path(path)
    dt = datetime.now().strftime("%d-%m-%y-%H%M")
    Printer.from_tokens(structs).to_file(Path(f'{dt}.hpp'))
    written_structs = ', '.join(struct.name for struct in structs)
    console.print(
        "[b yellow]Wrote TtoDebug, TtoString,"
        f" TfromString and newT for {written_structs}",
        justify='center',
    )
    console.log("[b white]Done! Bye! 👋", justify='center')


@app.command(
    name='files',
)
def open_excel(
    path: Path = Argument(
        DEFAULT_EXCEL,
        help="La dirección del .xlsx",
        dir_okay=False,
        resolve_path=True,
        exists=True,
    ),
    sheet: Optional[str] = Option(
        None, '-s', '--sheet', help="El nombre de la solapa/sheet"
    ),
    read: bool = Option(True, help="Lee las estructuras guardadas en el .dat"),
) -> None:
    """
    Por default, abre el excel `AlgoritmosFiles.xlsx` en la carpeta en la que
    estén y lee todas sus solapas.

    Si el excel está en otro lugar, pueden especificar la dirección del archivo.xlsx
    después del nombre del programa,
    ej: ayed files home/bocanada/Documents/AlgoritmosFiles.xlsx.

    Con -s o --sheet [SHEET] pueden especificar una solapa, siendo [SHEET] la solapa.

    Si utilizan --no-read, el programa no leerá los archivos para mostrarlos.
    """
    excel = Excel(path)
    excel.read(sheet=sheet)
    if sheet:
        f = excel.read_sheet()
        write_one(f, sheet_name=sheet, unpack=read)
    else:
        f = excel.read_sheets()
        write_many(f, unpack=read)
    console.log("[b white]Done! Bye! 👋", justify='center')


if __name__ == "__main__":
    app(prog_name='ayed')
