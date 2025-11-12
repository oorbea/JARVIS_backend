from abc import ABC, abstractmethod

class IWriterController(ABC):
    @abstractmethod
    def write_file(self, file_path: str, data: bytes) -> None:
        raise NotImplementedError