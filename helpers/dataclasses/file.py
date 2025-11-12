from dataclasses import dataclass

from enums.file_format import FileFormat

@dataclass
class FileData:
    path: str
    size: int
    format: FileFormat
    file_content: bytes
    metadata: dict | None = None