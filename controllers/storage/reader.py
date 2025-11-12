from abc import ABC, abstractmethod

class IReaderController(ABC):
    @abstractmethod
    def read_file(self, file_path: str) -> bytes:
        raise NotImplementedError