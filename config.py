

# configuration variables

# intrumet names
RS_DAQ_NAME = 'TCPIP::172.16.39.12::INSTR'
RS_PSU_NAME = "TCPIP::172.16.39.14::5025::SOCKET"
CV180_IP = '192.168.1.180' #'192.168.1.180' # ip addr ???
T12S_IP = '192.168.1.12'
CV180_PORT = 1231
T12S_PORT = 1231

CV180_connection_timeout = 10 # seconds

EXT_RS232 = "/dev/ext_rs232"
TTL_RS232_8XG = '/dev/ttl_rs232_8xg'
RS485_8XG = '/dev/rs485_8xg'
TTL_RS232_T12 = '/dev/ttl_rs232_t12'
RS485_T12 = '/dev/rs485_t12'
BAUDRATE_SERIAL = int(115200)
TIMEOUT_SERIAL = float(0.050)

# status
IDLING = "7000" # no command in execution
BUSY = "7002" # follow up call during active execution of a test without further details (measuring is ongoing, no results available)

test_finished_ok = "0000" # test finished, step overall result OK
test_finished_nok = "0001" # test finished, but step ovarall result NOK

process_start_response_with_header = "7001" # test started, response includes header
ongoing_execution = "7100" # test is already running

board_mismatch = "8201"
step_mismatch = "8202"
psu_connection_error = "8401"
psu_communication_error = "8402"
psu_reSet_values_error = "8403"
daq_connection_error = "8411"
daq_communication_error = "8412"
daq_reSet_values_error = "8413"
cv180_connection_error = "8421"
cv180_communication_error = "8422"
cv180_values_error = "8423"
fpga_programming_error = "8424"

test_file_not_found = "8601"
test_file_parse_error = "8602"
test_file_incorrect_values = "8603"

test_was_cancelled = "CANCELLED"
cancellation_success = test_finished_ok # 0x0000 sucess code
cancellation_successfuly_interrupted_test = "0010"


# !NOT TO CHANGE! config varriables (to prevent typos) !NOT TO CHANGE!
file_name = 'file_name'
test_script = 'test_script'
psu_settings = 'psu'
cv180_connection = 'cv180_connection'
t12s = False
out_gen = 'out_gen'
out = 'out'
voltage = 'voltage'
current = 'current'
# headers
default_header = "No.,Description,Actual,Nominal/Expected,Min.,Max,Unit,Result"




# > Power Supply Unit 
# DUT psu settings
DUT_PSU_CH = 1      # psu channel allocation
DUT_VOLTAGE = 24    
DUT_CURRENT = 2
DUT_CURRENT_AFTER_PROGRAMMING = 4
PELTIER_CURRENT = 6     


# AUX 24v
AUX_24V_PSU_CH = 2   
AUX_24V_VOLTAGE = 24
AUX_24V_CURRENT = 2

# AUX 5v
AUX_5V_PSU_CH = 3    
AUX_5V_VOLTAGE = 5 
AUX_5V_CURRENT = 2

# ch4 is empty
PSU_CH4 = 4           
#PSU_CH4_VOLTAGE = 0 
#PSU_CH4_CURRENT = 1 # can't be 0

psu_channel_list = [DUT_PSU_CH, AUX_24V_PSU_CH, AUX_5V_PSU_CH, PSU_CH4]

channel_off = { out: False, voltage: 0, current: 1 } # current range: [0.001-5/10]

psu_off = { 
    out_gen: False, 
    DUT_PSU_CH: channel_off,
    AUX_24V_PSU_CH: channel_off,
    AUX_5V_PSU_CH: channel_off,
    PSU_CH4: channel_off,
}


def validate_config(test_spec_dict): 
    for board in test_spec_dict:
        board_config = test_spec_dict[board]
        if file_name not in board_config:
            return f'{board} has no file specified'
        elif type(board_config[file_name]) != str:
            return f'{board} {file_name} must be string'
        board_config_array = list(board_config)
        board_config_array.remove(file_name)
        for test in board_config_array:
            test_config = board_config[test]
            if test_script not in test_config:
                return f'{board} - {test} has no test script'
            if psu_settings not in test_config:
                return f'{board} - {test} has no default psu settings'
            else:
                e = validate_psu_settings(board, test, test_config[psu_settings])
                if e:
                    return e
            if cv180_connection not in test_config:
                return f'{board} - {test} has not specified cv180 connection'    
    return None

def validate_psu_settings(board: str, test: str, settings: dict):
    #psu_settings_arr = psu_channel_list.copy()
    
    checked_channels = []

    if out_gen not in settings:
        return f'{board} - {test} - psu has no default output general specified'
    
    settings_channel_list = list(settings)
    settings_channel_list.remove(out_gen)
    for psu_channel in settings_channel_list:
        if psu_channel not in psu_channel_list:
            return f'{board} - {test} - "{psu_channel}" channel does not exist on psu'
        psu_channel_settings = settings[psu_channel]
        if out not in psu_channel_settings:
            return f'{board} - {test} - no default output on channel {psu_channel} spefified'
        elif type(psu_channel_settings[out]) != bool:
            return f'{board} - {test} - {out} on channel {psu_channel} must be boolean'
        if voltage not in psu_channel_settings:
            return f'{board} - {test} - no default voltage on channel {psu_channel} spefified'
        elif type(psu_channel_settings[voltage]) != float and type(psu_channel_settings[voltage]) != int:
            return f'{board} - {test} - {voltage} on channel {psu_channel} {voltage} must be integer or float'
        if current not in psu_channel_settings:
            return f'{board} - {test} - "{psu_channel}" has no default current spefified'
        elif type(psu_channel_settings[current]) != float and type(psu_channel_settings[current]) != int:
            return f'{board} - {test} - {current} on channel {psu_channel} {current} must be integer or float'
        checked_channels.append(psu_channel)
    if len(checked_channels) != len(psu_channel_list):
        missing_channels = []
        for channel in psu_channel_list:
            if channel not in checked_channels:
                missing_channels.append(str(channel))
        missing_channels_str = ', '.join(missing_channels)
        return f'{board} - {test} - {psu_settings} has missing channel(s): {missing_channels_str}'
    return None