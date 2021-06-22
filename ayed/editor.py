from os import environ, name
from pathlib import Path
from shutil import which
from typing import Optional
from attr import dataclass

WIN = name == "nt"


@dataclass
class Editor:
    extension: Optional[str] = ".cpp"
    path: Optional[str] = None
    env: Optional[dict[str, str]] = None

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
        from subprocess import Popen

        editor = self.get_editor()
        env: Optional[dict[str, str]] = None

        if self.env:
            env = env.copy()  # type: ignore
            env.update(self.env)

        try:
            c = Popen(f'{editor} "{filename}"', env=env, shell=True)
            exit_code = c.wait()
            if exit_code != 0:
                raise SystemExit(f"{editor}: Editing failed")
        except OSError as e:
            raise OSError(f"{editor}: Editing failed: {e}") from e

    def edit(self, text: Optional[str]) -> Optional[str]:
        import tempfile

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

        fd, name = tempfile.mkstemp(prefix="editor-", suffix=self.extension)

        try:
            with open(fd, "wb") as f:
                f.write(data)

            self.edit_file(name)

            with open(name, "rb") as f:
                rv = f.read()

            if isinstance(text, (bytes, bytearray)):
                return rv.decode("utf-8-sig").replace("\r\n", "\n")

            return rv.decode("utf-8-sig").replace("\r\n", "\n")
        finally:
            Path(name).unlink()
