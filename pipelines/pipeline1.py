from data_blocks.drivers.erpnext_driver import ERPNextDriver
from data_blocks.integrators.dummy import DummyIntegrator
import pandas as pd

from data_blocks.base_pipeline import BasePipeline



class Pipeline1(BasePipeline):

    def run(self, *args:pd.DataFrame, **kwargs) -> pd.DataFrame:
        print("Hello from pipeline1")

        driver = ERPNextDriver(config={})
        data_set = driver.fetch_data()

        integrator = DummyIntegrator()

        output = integrator.integrate(data_set1=data_set, data_set2=data_set)



        return output

    