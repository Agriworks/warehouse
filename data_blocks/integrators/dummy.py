from data_blocks.base_data_integrator import BaseDataIntegrator
import pandas as pd

class DummyIntegrator(BaseDataIntegrator):
    def integrate(self, data_set1, data_set2) -> pd.DataFrame:
        # Integrate data
        return pd.DataFrame({"test": [1, 2, 3]})
