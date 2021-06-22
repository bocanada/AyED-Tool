from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional
from unicodedata import category, normalize

from rich.console import Console
from rich.table import Table
from rich.traceback import install

from ayed.editor import Editor

console = Console()

install(console=console)  # install traceback hook


@dataclass
class NoStructException(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


def edit(text: str) -> str:
    editor = Editor()
    code = editor.edit(text)
    if code is None:
        raise NoStructException("Couldn't parse the struct.")
    return code.split(text, 1)[1].strip()


def add_includes(*, libs: list[str]) -> str:
    lib = ["#include " + (f"<{lib}>" if "/" not in lib else f'"{lib}"') for lib in libs]
    return "\n".join(lib) + "\n"


def build_cfn(
    ret: str,
    name: str,
    *,
    params: Optional[list[str]] = None,
    body: Optional[list[str]] = None,
    vret: Optional[str] = None,
) -> str:
    """Builds a Cpp function"""
    if body:
        body = ["  " + line for line in body]
    if ret == "string":
        ret = "std::string"
    return (
        # returntype functionName(type varname, for all params)
        f'{ret} {name}({", ".join(params or [])})\n'
        + "{\n"  # {
        + (";\n".join(body) + ";\n" if body else "")  # function body
        + (f"  return {vret};\n" if ret != "void" else "")
        + "};\n"  # return varname;  # };
    )


def create_table(
    title: str, columns: Iterable[Any], rows: Iterable[Any] = None
) -> Table:
    table = Table(
        highlight=True,
        title=title,
        title_justify="center",
        show_header=True,
        show_lines=True,
    )
    for col in columns:
        table.add_column(col, justify="center")
    if rows:
        for row in rows:
            table.add_row(row)
    return table


def sanitize_name(fname: str) -> str:
    return "".join(
        c for c in normalize("NFD", fname) if category(c) != "Mn" and c != " "
    )
