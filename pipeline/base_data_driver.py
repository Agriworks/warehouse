import abc 
import pandas as pd


class BaseDataDriver(abc.ABC):
    @abc.abstractmethod
    def fetch_data(self) -> pd.DataFrame:
        raise NotImplementedError()