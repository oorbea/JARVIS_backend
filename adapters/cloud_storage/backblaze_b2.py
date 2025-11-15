from io import BytesIO
import traceback

from b2sdk._internal.exception import FileNotPresent
from b2sdk.v2 import InMemoryAccountInfo, B2Api, Bucket
from flask import current_app as app

from adapters.cloud_storage.interface import ICloudStorageAdapter
from exceptions.cloud_storage import CloudStorageAuthorizationException, CloudStorageDownloadException, CloudStorageUploadException
from enums.file_format import FileFormat
from helpers.dataclasses.file import FileData


class BackblazeB2Adapter(ICloudStorageAdapter):
    __info:InMemoryAccountInfo
    __b2_api:B2Api
    __application_key_id:str
    __application_key:str
    __bucket_name:str

    def __init__(self, application_key_id: str = None, application_key: str = None, bucket_name:str = "jarvis") -> None:
        self.__info = InMemoryAccountInfo()
        self.__b2_api = B2Api(self.__info)
        self.__application_key_id = application_key_id or app.config.get("BACKBLAZE_B2_KEY_ID")
        self.__application_key = application_key or app.config.get("BACKBLAZE_B2_APPLICATION_KEY")
        self.__bucket_name = bucket_name

        try:
            self.__b2_api.authorize_account("production", self.__application_key_id, self.__application_key)
        except Exception as e:
            traceback.print_exc()
            raise CloudStorageAuthorizationException from e
        
    def upload_file(self, file: FileData) -> None:
        try:
            bucket:Bucket = self.__b2_api.get_bucket_by_name(self.__bucket_name)
            bucket.upload_bytes(file.file_content, file.path, file_info=file.metadata)
        except Exception as e:
            traceback.print_exc()
            raise CloudStorageUploadException from e
        
    def download_file(self, file_path: str) -> FileData:
        try:
            bucket:Bucket = self.__b2_api.get_bucket_by_name(self.__bucket_name)
            downloaded_file = bucket.download_file_by_name(file_path)

            buffer = BytesIO()
            downloaded_file.save(buffer)
            file_content = buffer.getvalue()

            file_extension = file_path.split('.')[-1].upper()
            file_format = FileFormat[file_extension]

            return FileData(
                path=file_path,
                size=len(file_content),
                format=file_format,
                file_content=file_content,
                metadata=downloaded_file.download_version.file_info or None
            )
        except FileNotPresent as e:
            traceback.print_exc()
            raise FileNotFoundError(
                f"File '{file_path}' not found in bucket '{self.__bucket_name}'."
            ) from e
        except KeyError as e:
            traceback.print_exc()
            raise ValueError(f"Unsupported file format for '{file_path}'.") from e
        except Exception as e:
            traceback.print_exc()
            raise CloudStorageDownloadException from e
