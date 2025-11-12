from abc import ABC, abstractmethod
from controllers.storage.storage import IStorageController, LocalStorageController
from controllers.storage.reader import IReaderController, LocalReaderController
from controllers.storage.writer import IWriterController, LocalWriterController

class IControllerFactory(ABC):
    @abstractmethod
    def get_storage_controller(self) -> IStorageController:
        raise NotImplementedError

    @abstractmethod
    def get_reader_controller(self) -> IReaderController:
        raise NotImplementedError

    @abstractmethod
    def get_writer_controller(self) -> IWriterController:
        raise NotImplementedError
    
class LocalStorageControllerFactory(IControllerFactory):
    __reader_controller: IReaderController | None
    __writer_controller: IWriterController | None
    __storage_controller: IStorageController | None
    def __init__(self,
                 storage_controller: IStorageController | None = None,
                 reader_controller: IReaderController | None = None,
                 writer_controller: IWriterController | None = None):
        self.__storage_controller = storage_controller
        self.__reader_controller = reader_controller
        self.__writer_controller = writer_controller

    def get_storage_controller(self) -> IStorageController:
        if self.__storage_controller:
            return self.__storage_controller
        self.__storage_controller = LocalStorageController(
            reader=self.get_reader_controller(),
            writer=self.get_writer_controller()
        )
        return self.__storage_controller

    def get_reader_controller(self) -> IReaderController:
        if not self.__reader_controller:
            self.__reader_controller = LocalReaderController()
        return self.__reader_controller

    def get_writer_controller(self) -> IWriterController:
        if not self.__writer_controller:
            self.__writer_controller = LocalWriterController()
        return self.__writer_controller