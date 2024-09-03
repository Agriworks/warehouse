import abc
import pandas as pd

class BaseDataIntegrator(abc.ABC):
    
    @abc.abstractmethod
    def integrate(self, data_set1: pd.DataFrame, data_set2: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError()