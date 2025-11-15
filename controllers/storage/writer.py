from abc import ABC, abstractmethod

from adapters.cloud_storage.backblaze_b2 import BackblazeB2Adapter
from adapters.cloud_storage.interface import ICloudStorageAdapter

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

class CloudWriterController(IWriterController):
    def write_file(self, file_path: str, data: bytes) -> None:
        adapter:ICloudStorageAdapter = BackblazeB2Adapter()
        return adapter.upload_file(file_path, data)