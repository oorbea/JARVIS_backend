from abc import ABC

from controllers.storage.reader import CloudReaderController, IReaderController, LocalReaderController
from controllers.storage.writer import CloudWriterController, IWriterController, LocalWriterController
from helpers.dataclasses.file import FileData

class StorageController(ABC):
    _reader: IReaderController
    _writer: IWriterController

    def read_file(self, file_path: str) -> FileData:
        return self._reader.read_file(file_path)
    
    def write_file(self, file_path: str, data: bytes) -> None:
        return self._writer.write_file(file_path, data)
    
class LocalStorageController(StorageController):
    def __init__(self,
                 reader: LocalReaderController | None = None,
                 writer: LocalWriterController | None = None):
        self._reader = reader if reader else LocalReaderController()
        self._writer = writer if writer else LocalWriterController()

class CloudStorageController(StorageController):
    def __init__(self,
                 reader: CloudReaderController | None = None,
                 writer: CloudWriterController | None = None):
        self._reader = reader if reader else CloudReaderController()
        self._writer = writer if writer else CloudWriterController()