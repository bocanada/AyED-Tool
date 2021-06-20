from pathlib import Path
from ayed.tool import Tokenizer
from pytest import raises


def test_build_cfn():
    from ayed.utils import build_cfn

    f = """int fib(int n)\n{
  return fib(n - 1) + fib(n - 2);
};
"""
    assert f == build_cfn(
        'int', 'fib', params=['int n'], vret='fib(n - 1) + fib(n - 2)'
    )


def test_includes():
    from ayed.utils import add_includes

    r = "#include <stdio>\n#include \"libreria/something/something\"\n"
    assert r == add_includes(libs=['stdio', 'libreria/something/something'])


def test_editoerror():
    from ayed.utils import edit

    with raises(SystemExit) as e:
        edit("#code here")


def test_tfrom_str() -> None:
    result = """Equipo equipoFromString(std::string s)
{
  Equipo x{};
  std::string t0 = getTokenAt(s, '-', 0);
  x.idEq = stoi(t0);
  std::string t1 = getTokenAt(s, '-', 1);
  strcpy(x.nombre, t1.c_str());
  std::string t2 = getTokenAt(s, '-', 2);
  x.puntos = stoi(t2);
  return x;
};
"""
    t = Tokenizer.from_path(Path('tests/structs/structs.cpp'))
    r = t[0].from_str()
    assert r == result


def test_todebug() -> None:
    result = """std::string equipoToDebug(Equipo e)
{
  std::stringstream sout;
  sout << "Equipo" << "{";
  sout << "idEq : " << e.idEq << ", ";
  sout << "nombre : " << e.nombre << ", ";
  sout << "puntos : " << e.puntos;
  sout << "};";
  return sout.str();
};
"""
    t = Tokenizer.from_path(Path('tests/structs/structs.cpp'))
    r = t[0].to_debug()
    assert r == result


def test_from_str() -> None:
    result = """Equipo equipoFromString(std::string s)
{
  Equipo x{};
  std::string t0 = getTokenAt(s, '-', 0);
  x.idEq = stoi(t0);
  std::string t1 = getTokenAt(s, '-', 1);
  strcpy(x.nombre, t1.c_str());
  std::string t2 = getTokenAt(s, '-', 2);
  x.puntos = stoi(t2);
  return x;
};
"""
    tr = """struct Equipo {
  int idEq;
  char nombre[20];
  int puntos;
};"""
    t = Tokenizer.from_str(tr)
    assert str(t[0].from_str()) == result


def test_to_str() -> None:
    result = """std::string equipoToString(Equipo e)
{
  return std::to_string(e.idEq)+'-'+(e.nombre)+'-'+std::to_string(e.puntos);
};
"""
    t = Tokenizer.from_path(Path('tests/structs/structs.cpp'))
    assert t[0].to_str() == result


def test_fromstr_with_structs() -> None:
    result = '''NEquipo nequipoFromString(std::string s)
{
  NEquipo x{};
  std::string t0 = getTokenAt(s, '-', 0);
  x.e = equipoFromString(t0);
  std::string t1 = getTokenAt(s, '-', 1);
  x.npuntos = stoi(t1);
  return x;
};
'''
    t = Tokenizer.from_path(Path('tests/structs/structs3.cpp'))
    assert str(t[0].from_str()) == result


def test_tostr_with_structs() -> None:
    result = '''std::string nequipoToString(NEquipo n)
{
  return equipoToString(n.e)+'-'+std::to_string(n.npuntos);
};
'''
    t = Tokenizer.from_path(Path('tests/structs/structs3.cpp'))
    assert str(t[0].to_str()) == result
