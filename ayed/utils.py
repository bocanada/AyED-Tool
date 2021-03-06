from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from tempfile import mkstemp
from typing import Any, Iterable, Optional
from unicodedata import category, normalize

from rich.console import Console
from rich.table import Table
from rich.traceback import install

console = Console()

install(console=console)  # install traceback hook


def add_includes(*, libs: list[str]) -> str:
    """
    Builds a str of includes,

    >>> add_includes(libs=[cstring, string, stdio])
    '''#include <cstring>
    #include <string>
    #include stdio
    '''
    """
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
    return "\n".join(
        [
            # returntype functionName(type varname, for all params)
            f'{ret} {name}({", ".join(params or [])})',
            "{",  # {
            (";\n".join(body) + ";" if body else ""),  # function body
            (f"  return {vret};" if ret != "void" else ""),
            "};\n",  # return varname;  # };
        ]
    )


def create_table(
    title: str, columns: Iterable[Any], rows: Iterable[Any] = None
) -> Table:
    """Creates a table to print out all the written structs"""
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
    """Removes all spaces, diacritics and tildes from a str"""
    return "".join(
        c for c in normalize("NFD", fname) if category(c) != "Mn" and c != " "
    )


@contextmanager
def tmpfile(prefix: str, suffix: str | None):

    fd, name = mkstemp(prefix=prefix, suffix=suffix)
    name = Path(name)
    try:
        yield fd, name
    finally:
        name.unlink()
