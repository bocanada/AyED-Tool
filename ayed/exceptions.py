from attr import dataclass


@dataclass
class NoStructException(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class ReadSheetException(Exception):
    message: str

    def __str__(self) -> str:
        return self.message
