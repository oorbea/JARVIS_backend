from abc import ABC, abstractmethod

class IReaderController(ABC):
    @abstractmethod
    def read_file(self, file_path: str) -> bytes:
        """
        Reads a file and returns its contents as bytes.

        Args:
            file_path (str): The path to the file to be read.
        Returns:
            bytes: The contents of the file.
        Raises:
            FileNotFoundError: If the file does not exist.
            OSError: If there is an error reading the file.
        """
        raise NotImplementedError
    
class LocalReaderController(IReaderController):
    def read_file(self, file_path: str) -> bytes:
        with open(file_path, 'rb') as file:
            return file.read()
        
class CloudReaderController(IReaderController):
    def read_file(self, file_path: str) -> bytes:
        #TODO: Implement cloud storage reading logic
        raise NotImplementedError("CloudReaderController is not implemented yet.")