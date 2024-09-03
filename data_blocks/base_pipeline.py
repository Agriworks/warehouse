
from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd

class BasePipeline(ABC):

    @abstractmethod
    def run(self, *args:pd.DataFrame, **kwargs) -> Optional[pd.DataFrame]:        
        raise NotImplementedError()
    
    @abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError()