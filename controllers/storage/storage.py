from abc import ABC, abstractmethod

class IStorageController(ABC):
    @abstractmethod
    def read_file(self, file_path: str) -> bytes:
        raise NotImplementedError
    
    @abstractmethod
    def write_file(self, file_path: str, data: bytes) -> None:
        raise NotImplementedError