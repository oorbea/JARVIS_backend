from abc import ABC


class CloudStorageException(Exception, ABC):
    """Base exception for cloud storage errors."""
    def __init__(self, message: str = "An error occurred with cloud storage.") -> None:
        super().__init__(message)

class CloudStorageAuthorizationException(CloudStorageException):
    """Exception for cloud storage authorization errors."""
    def __init__(self, message: str = "Failed to authorize with cloud storage.") -> None:
        super().__init__(message)

class CloudStorageUploadException(CloudStorageException):
    """Exception for cloud storage upload errors."""
    def __init__(self, message: str = "Failed to upload file to cloud storage.") -> None:
        super().__init__(message)

class CloudStorageDownloadException(CloudStorageException):
    """Exception for cloud storage download errors."""
    def __init__(self, message: str = "Failed to download file from cloud storage.") -> None:
        super().__init__(message)