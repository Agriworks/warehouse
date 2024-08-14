from operations.drivers.erpnext_driver import ERPNextDriver
from operations.integrators.dummy import DummyIntegrator
from pipeline.base_data_integrator import BaseDataIntegrator
import pandas as pd



def entrypoint() -> pd.DataFrame:
    print("Hello from pipeline1")

    driver = ERPNextDriver(config={})
    data_set = driver.fetch_data()

    integrator = DummyIntegrator()

    output = integrator.integrate(data_set1=data_set, data_set2=data_set)



    return output

    