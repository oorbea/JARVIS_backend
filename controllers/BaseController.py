from abc import ABC, abstractmethod

class BaseController(ABC):
    """Base class for all controllers."""

    __settings:dict

    def __init__(self, **kwargs):
        self.__settings = kwargs or {}

    def get_settings(self) -> dict:
        return self.__settings
    
    def set_settings(self, **kwargs):
        self.__settings.update(kwargs)

    def get_one_setting(self, key:str):
        return self.__settings.get(key, None)
    
    @abstractmethod
    def run(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method.")
    
    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)