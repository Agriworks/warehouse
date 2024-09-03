import pandas as pd

from data_blocks.base_data_driver import BaseDataDriver


class ERPNextDriver(BaseDataDriver):
    def __init__(self, config):
        self.config = config

    def fetch_data(self) -> pd.DataFrame:
        # Fetch data from ERPNext
        return pd.DataFrame({"data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
