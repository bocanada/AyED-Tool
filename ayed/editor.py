from __future__ import annotations

from os import environ, name
from shutil import which
from subprocess import Popen
from ayed.utils import tmpfile
from ayed.exceptions import NoStructException

from attr import dataclass

WIN = name == "nt"


@dataclass
class Editor:
    extension: str | None = ".cpp"
    path: str | None = None
    env: dict[str, str] | None = None

    def get_editor(self) -> str:
        if self.path is not None:
            return self.path
        for key in "VISUAL", "EDITOR":
            rv = environ.get(key)
            if rv:
                return rv
        if WIN:
            return "notepad"
        for editor in ("nvim", "vim", "nano"):
            if which(editor) is not None:
                return editor
        return "vi"

    def edit_file(self, filename: str) -> None:

        editor = self.get_editor()

        try:
            c = Popen(f'{editor} "{filename}"', env=self.env, shell=True)
            exit_code = c.wait()
            if exit_code != 0:
                raise SystemExit(f"{editor}: Editing failed")
        except OSError as e:
            raise OSError(f"{editor}: Editing failed: {e}") from e

    def edit(self, text: str | None) -> str | None:

        if not text:
            data = b""
        elif isinstance(text, (bytes, bytearray)):
            data = text
        else:
            if text and not text.endswith("\n"):
                text += "\n"
            if WIN:
                data = text.replace("\n", "\r\n").encode("utf-8-sig")
            else:
                data = text.encode("utf-8")

        with tmpfile("editor-", self.extension) as (fd, name):
            with open(fd, "wb") as f:
                f.write(data)

            self.edit_file(name.absolute().as_posix())

            with name.open("rb") as f:
                rv = f.read()

            if isinstance(text, (bytes, bytearray)):
                return rv.decode("utf-8-sig").replace("\r\n", "\n")

            return rv.decode("utf-8-sig").replace("\r\n", "\n")


def edit(text: str) -> str:
    """Launches an editor with `text` on top of the file."""
    editor = Editor()
    code = editor.edit(text)
    if code is None:
        raise NoStructException("Couldn't parse the struct.")
    return code.split(text, 1)[1].strip()
