from typing import Optional


def add_includes(*, libs: list[str]) -> str:
    lib = ["#include " + (f'<{lib}>' if not "/" in lib else f'"{lib}"') for lib in libs]
    return '\n'.join(lib) + "\n"


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
    return (
        f'{ret} {name}({", ".join(params or [])})\n'  # returntype functionName(type varname, for all params)
        + '{\n'  # {
        + (';\n'.join(body) + ';\n' if body else '')  # function body
        + (f'  return {vret};\n' if ret != 'void' else '')
        + '};\n'  # return varname;  # };
    )
