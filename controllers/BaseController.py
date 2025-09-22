from abc import ABC


class BaseController(ABC):
    """Base class for all controllers."""

    __settings:dict

    def __init__(self, **kwargs):
        self.__settings = kwargs or {}