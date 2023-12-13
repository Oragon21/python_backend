import time
from threading import Thread, Event
from hmp4040 import hmp4040
from cv180 import CV180
from flask import Flask, jsonify, request
from flask_cors import CORS  # Import the CORS extension
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
from daq_wrapper import DAQM973A
from tests_cases import(
                test_5_2,
                test_5_3,
                test_5_4,
                test_5_5_1,
                test_5_5_2,
                test_5_5_3,
                test_5_5_4,
                test_5_5_5,
                test_5_5_6,
                test_5_5_7,
                test_5_6_1,
                test_5_6_2,
                test_5_6_3,
                test_5_6_4,
                test_5_7_1,
                test_5_7_2,
                test_5_7_3,
                )
from config import *

app = Flask(__name__)

# Enable CORS for the entire application
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})

# Add a decorator to ensure CORS headers are added to every response
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://127.0.0.1:5500'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

# Add an OPTIONS route to handle preflight requests
@app.route('/', methods=['OPTIONS'])
def options():
    return '', 204

# a teszt végén ha error vagy NOK alap helyzetbe állítás

# after test:
#   (in every case) reset daq
#   if a test succeed we leave psu turned on
#   else (test fails = returns nok or error) we turn psu off


test_spec_dict = {
    "FANC": {
        file_name: "measurements.xlsx",
        "52": {
            test_script: test_5_2,
            psu_settings: psu_off,
            cv180_connection: False,
            t12s: False,
        },
        "53": {
            test_script: test_5_3,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: channel_off,
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: False,
            t12s: False,
        },
        "54": {
            test_script: test_5_4,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: {out: True, voltage: DUT_VOLTAGE, current: DUT_CURRENT},
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: False,
            t12s: False,
        },
        "551": {
            test_script: test_5_5_1,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: {out: True, voltage: DUT_VOLTAGE, current: DUT_CURRENT},
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: False,
            t12s: False,
        },
        "552": {  # Pushbutton ON test
            test_script: test_5_5_2,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: channel_off,  # channel will be turned on in the test
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: False,
            t12s: False,
        },
        "553": {  # Power Tree voltage measurement 
            test_script: test_5_5_3,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: {out: True, voltage: DUT_VOLTAGE, current: DUT_CURRENT},  # channel will be turned on in the test
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: False,
            t12s: False,
        },
        "554": {  # Pushbutton ON test
            test_script: test_5_5_4,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: channel_off,  # channel will be turned on in the test
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: False,
            t12s: False,
        },
        "555": {  # Input voltage and current measurement 2
            test_script: test_5_5_5,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH:  {out: False, voltage: DUT_VOLTAGE, current: DUT_CURRENT},
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: False,
            t12s: False,
        },
        "556": {  # Power Tree voltage measurement 2
            test_script: test_5_5_6,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: {out: True, voltage: DUT_VOLTAGE, current: DUT_CURRENT},
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: False,
            t12s: False,
        },
        "557": {  # DC Heating
            test_script: test_5_5_7,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: {out: True, voltage: DUT_VOLTAGE, current: DUT_CURRENT},
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: True,
            t12s: False,
        },
        "561": {  # Pressure measurement
            test_script: test_5_6_1,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: {out: True, voltage: DUT_VOLTAGE, current: DUT_CURRENT},
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: True,
            t12s: False,
        },
        "562": {  # Measuring optics
            test_script: test_5_6_2,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: {out: True, voltage: DUT_VOLTAGE, current: DUT_CURRENT},
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: True,
            t12s: False,
        },
        "563": {  # Peltier driver
            test_script: test_5_6_3,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: {out: True, voltage: DUT_VOLTAGE, current: DUT_CURRENT},
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: True,
            t12s: False,
        },
        "564": {  # Pump
            test_script: test_5_6_4,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: {out: True, voltage: DUT_VOLTAGE, current: DUT_CURRENT},
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: True,
            t12s: False,
        },
        "571": {  # Interface additional module
            test_script: test_5_7_1,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: {out: True, voltage: DUT_VOLTAGE, current: DUT_CURRENT},
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: True,
            t12s: False,
        },
        "572": {  # RTC
            test_script: test_5_7_2,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: {out: True, voltage: DUT_VOLTAGE, current: DUT_CURRENT},
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: True,
            t12s: False,
        },
        "573": {  # RS-232
            test_script: test_5_7_3,
            psu_settings: {
                out_gen: True,
                DUT_PSU_CH: {out: True, voltage: DUT_VOLTAGE, current: DUT_CURRENT},
                AUX_24V_PSU_CH: {
                    out: True,
                    voltage: AUX_24V_VOLTAGE,
                    current: AUX_24V_CURRENT,
                },
                AUX_5V_PSU_CH: {
                    out: True,
                    voltage: AUX_5V_VOLTAGE,
                    current: AUX_5V_CURRENT,
                },
                PSU_CH4: channel_off,
            },
            cv180_connection: True,
            t12s: False,
        },
    },
   }

#
status = IDLING  # -> 7002 BUSY -> 0000/0001/errorCode -> 7000 IDLING
data: object = object()
error: str = str()

# currently running test variables
event: Event = Event()
board: str = str()
step: str = str()
# previously runned test's board, step, success
# previous_test: ( str, str, bool ) | None = None

# instruments
psu: hmp4040
daq: DAQM973A
cv180: CV180


def connect_psu():
    """
    description
    """
    global psu

    psu = hmp4040()
        
    try:
        psu = hmp4040()
    except Exception as e:
        print("Error: ", str(e))

    if not psu.connected:
        return {
            "status": psu_connection_error,
            "error": "Failed to connect to the PSU.",
        }

    return None

def connect_daq():
    global daq

    daq = DAQM973A()

    if not (daq.connected):
        return {"status": daq_connection_error, "error": daq.error}

    return None

def connect_cv180(connect: bool, t12s = False):
    global cv180
    cv180 = CV180(connect, t12s)
    if connect and not cv180.connected:
        return {
            "status": cv180_connection_error,
            "error": "Timeout expired."
            if cv180.connection_timeout
            else "Failed to connect to the CV180.",
        }
    return None

def return_result(result, before_programming):
    global event, status, data, error, step, board
    

    # previous_test = ( board, step, test_ok )
    # step, board = None

    if "data" in result:
        data = result["data"]
    if "error" in result:
        error = result["error"]

    status = result["status"]

    # if test returned error OR was unsuccesful(NOK), need to reset instruments
    if (before_programming):
        try:
            print("Before programming")
            #psu.set_settings(psu_off)
            #daq.reset()
        except:
            # can't do anything?
            pass
    else:
        try:
            print("After programming")
            #daq.reset()
        except:
            return { "status": daq_reSet_values_error, "error": 'Failed to reset DAQ.' }

    event = Event()

    print("done")

def process_start_request(boardType: str, stepNo: str, spare: str):  # ["8XG","521",""]
    global event, board, step, status, cv180

    # if test is already running
    if status is not IDLING:
        return {"status": ongoing_execution}
    
    # set the global status
    status = BUSY  # while connecting to the instruments and executing the command

    # validate boardType and stepNo
    if boardType not in test_spec_dict:
        status = IDLING
        return {"status": board_mismatch}
    elif stepNo not in test_spec_dict[boardType]:
        status = IDLING
        return {"status": step_mismatch}

    # globalize variables
    board = boardType
    step = stepNo

    # get the test's configuration
    default_configuration = test_spec_dict[board][stepNo]

    # connect to instruments

    # # psu
    # e = connect_psu()
    # print("Connect psu ", e)

    # if e:  # if error occured
    #     status = IDLING
    #     return e
    
    # # connect and reset daq
    # e = connect_daq()
    # print("Connect daq ", e)


    # if e:  # if error occured
    #     status = IDLING
    #     return e
    
    # # configure psu 
    # e = psu.set_settings(default_configuration[psu_settings])
    # print("PSU set settings ", e)

    # if e:  # if error occured
    #     status = IDLING
    #     return e
    
    # # cv180
    # e = connect_cv180(default_configuration[cv180_connection], default_configuration[t12s])
    # print("Connect cv180 ", e)

    # if e:  # if error occured
    #     status = IDLING
    #     return e

    # start thread
    event = Event()
    psu = None
    cv180 = None
    daq = None

    t = Thread(
        target=default_configuration[test_script],
        args=[event, test_spec_dict[board][file_name], return_result, psu, cv180, daq],
    )
    t.start()

    # return header
    return {
        "status": process_start_response_with_header,
        "header": {step: default_header},
    }

def result_request(*args):
    global status, data, error

    if status == IDLING or status == BUSY:
        return {"status": status}

    elif status == test_finished_ok or status == test_finished_nok:
        return_value = {"status": status, "data": data}
        status = IDLING
        data = None
        error = str()
        return return_value

    else:
        return_value = {"status": status, "error": error}
        status = IDLING
        data = None
        error = str()
        return return_value

def terminate_request(*args):
    """
    This function terminates the currently running test, turns off the powersupply, daq
    and clears the status!
    """
    global step, board, status, data, error

    # stop thread
    if type(event) == Event:
        event.set()
        while status != BUSY:
            pass

    # psu
    e = connect_psu()
    if e:  # if error was returned
        status = IDLING
        step = str()
        board = str()
        data = None
        error = str()
        return e
    else:
        psu.set_settings(psu_off)
    

    # daq
    e = connect_daq()
    if e:
        status = IDLING
        step = str()
        board = str()
        data = None
        error = str()
        return e
    else:
        daq.reset()
    

    # reset values and calculate return status
    return_status = cancellation_success
    if status != IDLING:
        status = IDLING
        step= str()
        board = str()
        data = None
        error = str()
        return_status = cancellation_successfuly_interrupted_test

    return {"status": return_status}

def main():
    print("Main")
    # validate config
    e = validate_config(test_spec_dict)
    if e:
        print(e)
        return

    print("config is correct, starting server...")
    app = Flask(__name__)

    CORS(app)

    @app.route("/", methods=["POST"])
    def rpc_handler():
        # Parse the JSON-RPC request
        json_data = request.get_json()
        method = json_data.get("method")
        params = json_data.get("params")

        # Call the appropriate RPC function based on the method
        if method == "process_start_request":
            return process_start_request(*params)
        elif method == "result_request":
            return result_request(*params)
        elif method == "terminate_request":
            return terminate_request(*params)
        else:
            return jsonify({"error": "Unknown method"}), 400

    # Start the server with CORS enabled
    
    app.add_url_rule("/", "process_start_request", process_start_request, methods=["POST"])
    app.add_url_rule("/", "result_request", result_request, methods=["POST"])
    app.add_url_rule("/", "terminate_request", terminate_request, methods=["POST"])
    
    app.run(host="localhost", port=1006)
    app.register_multicall_functions()
    app.serve_forever()
    # start server
    # server = SimpleJSONRPCServer(("localhost", 1006))
    # print("SERVER IP:", server.server_address)
    # server.register_multicall_functions()
    # server.register_function(process_start_request)
    # server.register_function(result_request)
    # server.register_function(terminate_request)
    # print("server started")
    # server.serve_forever()

if __name__ == "__main__":
    main()

"""
Functions called by PLC:

process_start_request: takes 3 argument: [ board_name: string, step_no: string, spare: currently just an empty string ]
    Its task is to start the test (according to the specified parameters).

    Script:
        is test already running? yes: return status ongoing_execution
        set status busy (it must be done fast, to prevent starting other tests while running)
        are the given parameters valid? no: reset status and return status board_mismatch or step_mismatch
        connect to the instuments. fail: reset status and return status and error message
        save given parameters to global varriables (this way other functions can read them)
        start thread
        return status process_start_response_with_header and the header

result_reqest: takes 1 parameter (but it is not used yet (empty string))
    It is called frequently, about every 30ms.
    Its task to return the current status and the availabe test results.

    Script
        if the status is idling or test is running
            return the status
        if the status is test finished
            return status and data
            reset status (IDLING), data and error varriables ( error is not used but keep it safe )
        if the status is error code:
            return status and error
            reset status, data and error varriables (data is not used)

terminate_request: takes 1 parameter (but it is not used yet (empty string))
    It is called when the all of the tests are done OR test is cancelled. (on the PLC you have the option to cancel the started test)
    Its task is to terminate every test running, turn instruments off.

    After it was called, the test's result is deleted and the status will be IDLING.

"""