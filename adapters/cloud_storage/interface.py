from abc import ABC, abstractmethod

from helpers.dataclasses.file import FileData

class ICloudStorageAdapter(ABC):
    @abstractmethod
    def upload_file(self, file: FileData) -> None:
        """
        Uploads a file to cloud storage.

        Args:
            file (FileData): The file data to upload.
        Raises:
            OSError: If there is an error uploading the file.
        """
        raise NotImplementedError

    @abstractmethod
    def download_file(self, file_path: str) -> FileData:
        """
        Downloads a file from cloud storage.

        Args:
            file_path (str): The path in cloud storage of the file to download.
        Returns:
            FileData: The metadata and contents of the downloaded file.
        Raises:
            FileNotFoundError: If the file does not exist in cloud storage.
        """
        raise NotImplementedError