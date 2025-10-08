from abc import ABC, abstractmethod

class BaseController(ABC):
    """Base class for all controllers."""    
    @abstractmethod
    def run(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method.")
    
    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)