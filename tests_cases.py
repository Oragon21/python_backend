from datetime import datetime
import time
import re
import array as arr
import threading
from threading import Event
from urllib import response
import test_step_parser as tsp
import excel_sheet_read as esr
import subprocess
import pandas as pd
from hmp4040 import *
from cv180 import CV180, sterilize_cv180_response, sterilize_response
from daq_wrapper import *
from config import (
    DUT_PSU_CH,
    DUT_VOLTAGE,
    DUT_CURRENT,
    RS485_8XG,
    EXT_RS232,
    psu_off,
    test_finished_ok,
    test_finished_nok,
    test_was_cancelled,
    cv180_values_error,
    daq_communication_error,
    fpga_programming_error,

)


def validate_cv180_response(cv180, cv180_command, expected_value, validation_function):
    """
    Validate a CV180 response against an expected value using a validation function.

    :param cv180: CV180 object for communication with a device
    :param cv180_command: Command to send to the CV180
    :param expected_value: Expected value for validation
    :param validation_function: Function to validate the response
    :return: Tuple containing a boolean flag indicating validation result and the response
    """

    result, error = cv180.send_and_receive(cv180_command)
    if error:
        return None, error

    result = sterilize_cv180_response(cv180_command, result)
    step_ok_flag = validation_function(result, expected_value)
    return step_ok_flag, result


def validate_string_result(result, expected_value):
    """
    Validate a string result against an expected string value.

    :param result: Result to validate
    :param expected_value: Expected string value
    :return: True if the result matches the expected value, False otherwise
    """

    return result == expected_value

def validate_range_result(result, expected_value):
    """
    Validate a numeric result within a specified range.

    :param result: Result to validate
    :param expected_value: Dictionary containing "min" and "max" values for the range
    :return: True if the result is within the range, False otherwise
    """

    return expected_value["min"] <= result <= expected_value["max"]

def perform_cv180_validation(step_id, values, validation_function):
    """
    Perform CV180 validation and return the result.

    :param step_id: Identifier for the validation step
    :param values: Dictionary containing validation parameters
    :param validation_function: Function to validate the response
    :return: Tuple containing a dictionary with validation results and a boolean flag indicating success
    """

    name = values["name"]
    cv180_command = values["cv180_command"]
    cv180 = values["cv180"]
    expected_value = values["expected"]

    step_ok_flag, result = validate_cv180_response(
        cv180, cv180_command, expected_value, validation_function
    )

    return {
        step_id: f'{name},{result},{expected_value},-,-,-,{"OK" if step_ok_flag else "NOK"}'
    }, step_ok_flag

def __cv180_string_validation(step_id, values):
    """
    Perform CV180 string validation.

    :param step_id: Identifier for the validation step
    :param values: Dictionary containing validation parameters
    :return: Tuple containing a dictionary with validation results and a boolean flag indicating success, and an error (if any)
    """

    name = values["name"]
    expected = values["expected"]
    cv180_command = values["cv180_command"]
    cv180: CV180 = values["cv180"]

    result, error = cv180.send_and_receive(cv180_command)
    if error:
        return None, error

    result = sterilize_cv180_response(cv180_command, result)
    print("String validation result: ", result)
    step_ok_flag = result == expected
    # set_test_ok_flag(step_ok_flag)

    return (
        {
            step_id: f'{name},{result},{expected},-,-,-,{"OK" if step_ok_flag else "NOK"}'
        },
        step_ok_flag,
    ), None

def __cv180_range_validation(step_id, values):
    """
    Perform CV180 range validation.

    :param step_id: Identifier for the validation step
    :param values: Dictionary containing validation parameters
    :return: Tuple containing a dictionary with validation results and a boolean flag indicating success, and an error (if any)
    """

    name = values["name"]
    nominal = values["nom"]
    min = values["min"]
    max = values["max"]
    unit = values["unit"]
    cv180_command = values["cv180_command"]
    cv180: CV180 = values["cv180"]

    result, error = cv180.send_and_receive(cv180_command)
    if error:
        return None, error
    print('Result before:    ', result)
    
    result = sterilize_cv180_response(cv180_command, result)
    print('RESULT     ', result)
    step_ok_flag = result >= min and result <= max

    return (
        {
            step_id: f'{name},{format(result, ".8f")},{nominal},{format(min, ".8f")},{format(max, ".8f")},{unit},{"OK" if step_ok_flag else "NOK"}'
        },
        step_ok_flag,
    ), None

def t12s_validation(step_id, values):
    """
    Perform T12S validation.

    :param step_id: Identifier for the validation step
    :param values: Dictionary containing validation parameters
    :return: Tuple containing a dictionary with validation results and a boolean flag indicating success, and an error (if any)
    """

    name = values["name"]
    expected = values["expected"]
    cv180_command = values["cv180_command"]
    cv180: CV180 = values["cv180"]

    result, error = cv180.send_and_receive(cv180_command)
    if error:
        return None, error

    result = sterilize_cv180_response(cv180_command, result)
    step_ok_flag = result == expected
    # set_test_ok_flag(step_ok_flag)

    return (
        {
            step_id: f'{name},{result},{expected},-,-,-,{"OK" if step_ok_flag else "NOK"}'
        },
        step_ok_flag,
    ), None

def extract_ip_address(response: str):
    pattern = r"\d+\.\d+\.\d+\.\d+"
    match = re.search(pattern, response)

    if match:
        ip_address = match.group()
        return ip_address
    else:
        return None

def test_5_2(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):
    result_log = {
        "52": f"Returned log from the server!"
    }
    return_result(
        {
            "status": test_finished_ok,
            "data": result_log,
        },
        False
    )

def test_5_3(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_4(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_5_1(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_5_2(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_5_3(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_5_4(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_5_5(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_5_6(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_5_7(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_6_1(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_6_2(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_6_3(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_6_4(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_7_1(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_7_2(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)

def test_5_7_3(
    event: Event, file_name, return_result, psu: hmp4040, cv180: CV180, daq: DAQM973A
):

    return_result(result, True)