from abc import ABC, abstractmethod

from helpers.dataclasses.file import FileData
from enums.file_format import FileFormat

class IReaderController(ABC):
    @abstractmethod
    def read_file(self, file_path: str) -> FileData:
        """
        Reads a file and returns its contents as bytes.

        Args:
            file_path (str): The path to the file to be read.
        Returns:
            FileData: The metadata and contents of the file.
        Raises:
            FileNotFoundError: If the file does not exist.
            OSError: If there is an error reading the file.
        """
        raise NotImplementedError
    
class LocalReaderController(IReaderController):
    def read_file(self, file_path: str) -> FileData:
        with open(file_path, 'rb') as file:
            file_content = file.read()
            file_format = FileFormat[file_path.split('.')[-1].upper()]

            return FileData(
                path=file_path,
                size=len(file_content),
                format=file_format,
                file_content=file_content
            )

class CloudReaderController(IReaderController):
    def read_file(self, file_path: str) -> FileData:
        #TODO: Implement cloud storage reading logic
        raise NotImplementedError("CloudReaderController is not implemented yet.")