#!/usr/bin/env python
from __future__ import annotations
import os
import sys
from datetime import datetime
from pathlib import Path

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(
    os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__)))
)
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from rich.prompt import Confirm

from ayed.classes import Structs
from ayed.excel import Excel, write_many
from ayed.parser import Tokenizer
from ayed.printer import Printer
from ayed.utils import PromptPath, console, edit, prompt


def open_editor() -> Structs:
    SEPARATOR = '// write your code below'
    code = edit(SEPARATOR)
    return Tokenizer.from_str(code)


def ask_filepath() -> Structs:
    path = PromptPath.ask("Enter path to a .cpp[,.hpp,.c,.h]", console=console)
    return Tokenizer.from_path(path)


def coll_fn_gen() -> Structs:
    if Confirm.ask("[b]Open editor?", default='y'):
        structs = open_editor()
    else:
        structs = ask_filepath()
    dt = datetime.now().strftime("%d-%m-%y-%H%M")
    Printer.from_tokens(structs).to_file(Path(f'{dt}.hpp'))
    written_structs = ', '.join(struct.name for struct in structs)
    console.print(
        f"[b yellow]Wrote TtoDebug, TtoString, TfromString and newT for {written_structs}",
        justify='center',
    )
    return structs


def open_excel() -> None:
    path = PromptPath.ask(
        "[b]Enter path to a .xlsx[/b] 👀",
        console=console,
        default="AlgoritmosFiles.xlsx",
        show_default=True,
    )
    if Confirm.ask(
        "Por default, esto abrirá el excel y escribirá archivos en "
        "[i]output_files/[...].dat[/i]. Continuar?",
        default="y",
    ):
        excel = Excel(path)
        excel.read()
        f = excel.read_sheets()
        write_many(f)


def main() -> None:
    console.print(
        "1. [b white]Coll fn generator[/b white]\n2. [b white]Files generator[/b white]",
    )
    option = prompt.ask(
        console=console,
        prompt="[b]Option",
        choices=['1', '2'],
        show_choices=True,
    )
    if option == "1":
        coll_fn_gen()
    else:
        open_excel()
    console.log("[b white]Done! Bye! 👋", justify='center')


if __name__ == "__main__":
    main()
