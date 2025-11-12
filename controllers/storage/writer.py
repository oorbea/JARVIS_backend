from abc import ABC, abstractmethod

class IWriterController(ABC):
    @abstractmethod
    def write_file(self, file_path: str, data: bytes) -> None:
        """
        Writes data to a file.

        Args:
            file_path (str): The path to the file where data will be written.
            data (bytes): The data to write to the file.
        Raises:
            OSError: If there is an error writing to the file.
        """
        raise NotImplementedError
    
class LocalWriterController(IWriterController):
    def write_file(self, file_path: str, data: bytes) -> None:
        with open(file_path, 'wb') as file:
            file.write(data)