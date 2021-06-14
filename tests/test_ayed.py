from pathlib import Path
from ayed import __version__
from ayed import Tokenizer


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_tfrom_str() -> None:
    result = """Equipo equipoFromString(std::string e)
{
  Equipo x{};
  std::string t0 = getTokenAt(e, '-', 0);
  x.idEq = stoi(t0);
  std::string t1 = getTokenAt(e, '-', 1);
  strcpy(x.nombre, t1.c_str());
  std::string t2 = getTokenAt(e, '-', 2);
  x.puntos = stoi(t2);
  return x;
};
"""
    t = Tokenizer.from_path(Path('tests/structs/structs.cpp'))
    r = t.tokens[0].from_str()
    assert r == result
def test_todebug() -> None:
    result = """std::string equipoToDebug(Equipo e)
{
  std::stringstream sout;
  sout << "Equipo" << "{";
  sout << "idEq : " << e.idEq << ", ";
  sout << "nombre : " << e.nombre << ", ";
  sout << "puntos : " << e.puntos ;
  sout << "};";
  return sout.str();
};
"""
    t = Tokenizer.from_path(Path('tests/structs/structs.cpp'))
    r = t.tokens[0].to_debug()
    assert r == result

def test_from_str() -> None:
    result = """Equipo equipoFromString(std::string e)
{
  Equipo x{};
  std::string t0 = getTokenAt(e, '-', 0);
  x.idEq = stoi(t0);
  std::string t1 = getTokenAt(e, '-', 1);
  strcpy(x.nombre, t1.c_str());
  std::string t2 = getTokenAt(e, '-', 2);
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
    assert str(t.tokens[0].from_str()) == result


def test_to_str() -> None:
    result = """std::string equipoToString(Equipo e)
{
  return std::to_string(e.idEq)+'-'+(e.nombre)+'-'+std::to_string(e.puntos);
};
"""
    t = Tokenizer.from_path(Path('tests/structs/structs.cpp'))
    assert str(t.tokens[0].to_str('-')) == result


def test_fromstr_with_structs() -> None:
    result = '''NEquipo nequipoFromString(std::string n)
{
  NEquipo x{};
  std::string t0 = getTokenAt(n, '-', 0);
  x.e = equipoFromString(t0);
  std::string t1 = getTokenAt(n, '-', 1);
  x.npuntos = stoi(t1);
  return x;
};
'''
    t = Tokenizer.from_path(Path('tests/structs/structs3.cpp'))
    assert str(t.tokens[0].from_str()) == result


def test_tostr_with_structs() -> None:
    result = '''std::string nequipoToString(NEquipo n)
{
  return equipoToString(n.e)+'-'+std::to_string(n.npuntos);
};
'''
    t = Tokenizer.from_path(Path('tests/structs/structs3.cpp'))
    assert str(t.tokens[0].to_str('-')) == result
