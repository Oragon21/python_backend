import os
import pandas as pd
from threading import Event
from hmp4040 import hmp4040
from daq_wrapper import *
import re
from config import test_file_not_found, test_file_parse_error, test_file_incorrect_values, test_finished_ok, test_finished_nok, test_was_cancelled, psu_communication_error, daq_communication_error



def perform_test_steps(
    event: Event,
    file_name: str,
    test_step_name: str,
    psu: hmp4040,
    daq: DAQM973A
):
    """
    This function implements a parser for electrical component measurements. The script processes an input
    excel sheet. The format of the excel sheet is defined in the 8XG and T12S specification documents.

    This function implements measurements where either the R&S PSU or the DAQ973 is used.

    Input parameters:
    - file_name : the name (or path to the) excel workbook containing the test steps.
    - test_step_name : name of the excel sheet containing the test sequence. This parameter comes from the heading number from the specification document. e.g. 5.1.2
    - psu : R&S power supply
    - daq : DAQM973A instance used for the measurements

    Return value:
    - a dictionary including the status, data or error
    """
    # Initialize dictionaries
    column_dict = {
        0: "sequence_num",
        1: "sequence_name",
        2: "pcb_sig+",
        3: "pcb_sig-",
        4: "meas_sig+",
        5: "meas_sig-",
        6: "nominal",
        7: "min",
        8: "max",
        9: "unit",
    }

    def calculate_voltage_range(max):
        max = abs(max)
        return ( RANGE_VOLT_MILLI if max < RANGE_VOLT_MILLI else 
                 RANGE_VOLT_ONE if max < RANGE_VOLT_ONE else 
                 RANGE_VOLT_TEN if max < RANGE_VOLT_TEN else 
                 RANGE_VOLT_HUNDRED
                  )

    def calculate_resistance_range(max):
        max = abs(max)
        return (RANGE_OHM_HUNDRED if max <= RANGE_OHM_HUNDRED else
                 RANGE_KOHM_ONE if max <= RANGE_KOHM_ONE else
                 RANGE_KOHM_TEN if max <= RANGE_KOHM_TEN else
                 RANGE_KOHM_HUNDRED if max <= RANGE_KOHM_HUNDRED else
                 RANGE_MOHM_ONE if max <= RANGE_MOHM_ONE else
                 RANGE_MOHM_TEN if max <= RANGE_MOHM_TEN else
                 RANGE_MOHM_HUNDRED if max <= RANGE_MOHM_HUNDRED else
                 RANGE_GOHM_ONE)

    daq_range_dict = { "V": calculate_voltage_range, "Ω": calculate_resistance_range }

    daq_unit_dict = {"V": daq.measure_voltage_dc, "Ω": daq.measure_resistance}
    psu_unit_dict = {"V": psu.measure_voltage, "A": psu.measure_current}
    

    # Regexp for finding measurement device
    daq_regexp = r"DAQ[M]?\d+A_\d-CH[0-9]+_[HL]"
    psu_regexp = r"PS-CH\d+\s*\+"
    num_regexp = r"\d+"

    # Measurement fail flag
    meas_fail = False

    if not os.path.exists(file_name):
        return { "status": test_file_not_found, "error": f"{file_name} not found!" }

    # Read in excel sheet, convert column names
    ws = pd.read_excel(
        file_name, sheet_name=test_step_name, skiprows=2, header=None
    )
    ws.columns = range(len(ws.columns))
    ws.columns = [column_dict.get(col_key) for col_key in ws.columns]

    # measurements buffer
    measurements = []

    # results buffer
    result_log = {}

    # check values from excel sheet
    for index, row in ws.iterrows():

        # Extract values from the excel sheet row
        try:
            step_id = row["sequence_num"].strip()
            step_name = row["sequence_name"].strip()
            meas_signal = row["meas_sig+"].strip()
            unit = row["unit"].strip()
            nom = row["nominal"]
            min = row["min"]
            max = row["max"]
        except:
            return { "status": test_file_parse_error, "error": f'{test_step_name} sheet at row {index+2} has wrong vaules. (empty or number instead of text)' }
        
        if not step_id or not step_name or not meas_signal or not unit or (type(min) != int and type(min) != float) or (type(max) != int and type(max) != float):
            return { "status": test_file_parse_error, "error": f"Test file has empty fields or header is not correct on sheet {test_step_name}." }


        # DAQ measurement
        if re.match(daq_regexp, meas_signal):
            # Extract numbers from the string
            # daq_regexp defines 3 numbers in the string
            [daqid, slot, channel] = re.findall(num_regexp, meas_signal)
            if unit in daq_unit_dict:
                measurements.append({ "device": "daq", "step_id": step_id, "step_name": step_name, "nom": nom, "min": min, "max": max, "unit": unit, "slot": int(slot), "channel": int(channel) })
            else:
                return { "status": test_file_incorrect_values, "error": f"{step_id} - {step_name}, unit \"{unit}\" not paired to existing DAQ mearement function!" }
                

        # PSU measurement
        elif re.match(psu_regexp, meas_signal):
            [ channel ] = re.findall(num_regexp, meas_signal)
            if unit in psu_unit_dict:
                measurements.append({ "device": "psu", "step_id": step_id, "step_name": step_name, "nom": nom, "min": min, "max": max, "unit": unit, "slot": None, "channel": int(channel) })
            else:
                return { "status": test_file_incorrect_values, "error": f"{step_id} - {step_name}, unit \"{unit}\" not paired to existing PSU measurement function!" }
                
        else:
            return { "status": test_file_incorrect_values, "error": f'Measuring device "{meas_signal}" at {step_id} - "{step_name}" is unknown' }
      
    # measuring
    for measurement in measurements:

        # check if test was cancelled
        if event.is_set():
            return { "status": test_was_cancelled }
        
        # get values
        device: str = measurement['device']
        step_id: str = measurement['step_id']
        step_name: str = measurement['step_name']
        unit: str = measurement["unit"]
        slot: int  = measurement['slot']
        channel: int = measurement['channel']
        nom: float | int = measurement['nom']
        min: float | int = measurement['min']
        max: float | int  = measurement['max']


        # meas_val initialize
        meas_val = -99999999

        # call function
        if device == "daq":
            try:
                meas_method = daq_unit_dict[unit]
                daq_range_calculate_function = daq_range_dict[unit]
                meas_val = meas_method(slot, channel, daq_range_calculate_function(max))
            except:
                return { "status": daq_communication_error, "error": "Failed to communicate with the DAQ." }
        elif device == "psu":
            try:
                meas_method = psu_unit_dict[unit]
                meas_val = meas_method(channel)
            except:
                return { "status": psu_communication_error, "error": 'Failed to communicate with the PSU.' }
        # analyze
        if meas_val < min or meas_val > max:
            meas_fail = True
            result_stat = "NOK"
        else:
            result_stat = "OK"
        
        # log
        step_id = step_id.replace('.', '')
        result_log = { **result_log, step_id: f'"{step_name}",{meas_val},{nom},{min},{max},{unit},{result_stat}' }


    # return result
    result_status = test_finished_nok if meas_fail else test_finished_ok
    return { "status": result_status, "data": result_log }
