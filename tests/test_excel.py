from ayed.excel import Excel
from ayed.printer import ExcelPrinter
from typing import Generator
from pathlib import Path
from struct import Struct
from pytest import fixture


@fixture(autouse=True, scope="module")
def teardown() -> Generator[None, None, None]:
    yield
    for i in Path("output_files").glob("*.dat"):
        i.unlink()


def test_struct_write() -> None:
    excel = Excel(
        file_path="tests/structs/AlgoritmosFiles.xlsx", sheet="Compañía de aviación"
    )
    with ExcelPrinter(excel) as p:
        p.to_file()
    assert len(list(Path("output_files").glob("*.dat"))) == 3


def test_RESERVAS() -> None:
    should_equal = (
        (1, 2, 1),
        (3, 2, 2),
        (5, 1, 3),
        (2, 2, 1),
        (1, 3, 5),
        (3, 1, 3),
        (6, 1, 2),
        (2, 2, 2),
        (3, 3, 6),
        (1, 1, 1),
        (2, 1, 1),
        (7, 4, 5),
    )
    s = Struct("iii")
    with Path("output_files/RESERVAS.dat").open("rb") as vuelos:
        for tup in should_equal:
            packed_data = s.unpack(vuelos.read(s.size))
            assert packed_data == tup


def test_VUELOS() -> None:
    should_equal = (
        (1, 10, 1, 4),
        (2, 15, 2, 1),
        (3, 12, 4, 3),
        (4, 5, 3, 2),
    )
    s = Struct("iiii")
    with Path("output_files/VUELOS.dat").open("rb") as vuelos:
        for tup in should_equal:
            packed_data = s.unpack(vuelos.read(s.size))
            assert packed_data == tup


def test_CIUDADES() -> None:
    should_equal = (
        (1, b"Miami".ljust(20), 800),
        (2, b"Madrid".ljust(20), 2000),
        (3, b"Londres".ljust(20), 1500),
        (4, b"Paris".ljust(20), 700),
    )
    s = Struct("i20si")
    with Path("output_files/CIUDADES.dat").open("rb") as vuelos:
        for tup in should_equal:
            packed_data = s.unpack(vuelos.read(s.size))
            assert packed_data == tup


def test_EMISIONDETICKETS() -> None:
    excel = Excel(
        file_path="tests/structs/AlgoritmosFiles.xlsx", sheet="Emisión de tickets"
    )
    with ExcelPrinter(excel) as p:
        p.to_file()
    assert excel.sheet is not None
    assert len(list(Path("output_files").glob("*.dat"))) == 5


def test_PRODUCTOS() -> None:
    should_equal = (
        (1, b"Manteca ", 100.0, 1),
        (2, b"Leche".ljust(8), 80.0, 1),
        (3, b"Yogurt".ljust(8), 80.0, 1),
        (4, b"Escoba".ljust(8), 250.0, 2),
        (5, b"Detergen", 180.0, 2),
        (
            6,
            b"Trapo de",
            50.0,
            2,
        ),
        (7, b"Galletit", 100.0, 3),
        (8, b"Aceite".ljust(8), 180.0, 3),
        (9, b"Vinagre".ljust(8), 100.0, 3),
        (10, b"Sal".ljust(8), 50.0, 3),
    )
    s = Struct("i8sdi")
    with Path("output_files/PRODUCTOS.dat").open("rb") as prod:
        for tup in should_equal:
            packed_data = s.unpack(prod.read(s.size))
            assert packed_data == tup


def test_RUBROS() -> None:
    should_eq = (
        (1, b"Lacteo".ljust(20), 1),
        (2, b"Limpieza".ljust(20), 0.95),
        (3, b"Almacen".ljust(20), 1),
    )

    s = Struct("i20sd")
    with Path("output_files/RUBROS.dat").open("rb") as prod:
        for tup in should_eq:
            packed_data = s.unpack(prod.read(s.size))
            assert packed_data == tup
