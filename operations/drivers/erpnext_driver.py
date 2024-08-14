import pandas as pd

from pipeline.base_data_driver import BaseDataDriver


class ERPNextDriver(BaseDataDriver):
    def __init__(self, config):
        self.config = config

    def fetch_data(self) -> pd.DataFrame:
        # Fetch data from ERPNext
        pass
