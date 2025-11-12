from abc import ABC, abstractmethod

from controllers.storage.reader import LocalReaderController
from controllers.storage.writer import LocalWriterController

class IStorageController(ABC):
    @abstractmethod
    def read_file(self, file_path: str) -> bytes:
        raise NotImplementedError
    
    @abstractmethod
    def write_file(self, file_path: str, data: bytes) -> None:
        raise NotImplementedError
    
class LocalStorageController(IStorageController):
    __reader: LocalReaderController
    __writer: LocalWriterController

    def __init__(self,
                 reader: LocalReaderController | None = None,
                 writer: LocalWriterController | None = None):
        self.__reader = reader if reader else LocalReaderController()
        self.__writer = writer if writer else LocalWriterController()

    def read_file(self, file_path: str) -> bytes:
        return self.__reader.read_file(file_path)

    def write_file(self, file_path: str, data: bytes) -> None:
        self.__writer.write_file(file_path, data)