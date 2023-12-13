import os
import pandas as pd
from daq_wrapper import *
from config import test_file_not_found


def read_table(
    file_name: str,
    test_step_name: str,
):

    if not os.path.exists(file_name):
        return { "status": test_file_not_found, "error": f"{file_name} not found!" }

    # Read in excel sheet, convert column names
    ws = pd.read_excel(
        file_name, sheet_name=test_step_name, skiprows=2, header=None
    )

    ws.columns = range(len(ws.columns))
    return ws
