from config import RS_DAQ_NAME
import pyvisa
import time

# The addition modules are inserted into the following slots
DAQM901A_1_SLOT = 1
DAQM901A_2_SLOT = 2
DAQM907A_SLOT = 3
# Use this range for voltages less than 100mV
RANGE_VOLT_MILLI = 0.001
# Use this range for voltages less than 1V and more than 100mV
RANGE_VOLT_ONE = 1
# Use this range for voltages less than 10V and more than 1V
RANGE_VOLT_TEN = 10
# Use this range for voltages less than 100V and more than 10V
RANGE_VOLT_HUNDRED = 100
# Use this range for voltages less than 300V and more than 100V
RANGE_VOLT_THREE_HUNDRED = 300
# Use this range for resistances less than 100Ω
RANGE_OHM_HUNDRED = 1e2
# Use this range for resistances less than 1kΩ and more than 100Ω
RANGE_KOHM_ONE = 1e3
# Use this range for resistances less than 10kΩ and more than 1kΩ
RANGE_KOHM_TEN = 1e4
# Use this range for resistances less than 100kΩ and more than 10kΩ
RANGE_KOHM_HUNDRED = 1e5
# Use this range for resistances less than 1MΩ and more than 100kΩ
RANGE_MOHM_ONE = 1e6
# Use this range for resistances less than 10MΩ and more than 1MΩ
RANGE_MOHM_TEN = 1e7
# Use this range for resistances less than 100MΩ and more than 10MΩ
RANGE_MOHM_HUNDRED = 1e8
# Use this range for resistances less than 1GΩ and more than 100MΩ
RANGE_GOHM_ONE = 1e9

class DAQM973A:
    rm: pyvisa.ResourceManager
    instrument: pyvisa.Resource
    daqm901a_1: int
    daqm901a_2: int
    daqm907a: int
    connected: bool
    error: str

    def __init__(self):
        """
        This class implements a simple programming interface for the DAQ973A data acquisition system.

        Input parameters:
        - instr_addr: local IP address of the data acquisition system.
        """
        self.rm = pyvisa.ResourceManager()
        try:
            self.instrument = self.rm.open_resource(RS_DAQ_NAME)
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'
            # Predefined slot values for the different addition modules
            self.daqm901a_1 = DAQM901A_1_SLOT
            self.daqm901a_2 = DAQM901A_2_SLOT
            self.daqm907a = DAQM907A_SLOT
            self.connected = True
            self.reset()
            
        except Exception as e:
            self.connected = False
            self.error = e

    def __del__(self):
        if self.connected:
            self.instrument.close()

    def measure_voltage_dc(self, slot: int, channel: int, voltage_range: int):
        """
        This function returns the measured DC voltage on the selected channel on one of the DAQM901A multiplexers.

        Input parameters:
        - slot : the slot number where the DAQM901A module is inserted, should be DAQM01A_1_SLOT or DAQM01A_2_SLOT.
        - channel : selected channel number (1-20)
        - voltage_range : the range of the expected voltage. For the details of the constants see the comments above!
            possible values for voltage_range: RANGE_VOLT_MILLI, RANGE_VOLT_ONE, RANGE_VOLT_TEN, RANGE_VOLT_HUNDRED, RANGE_VOLT_THREE_HUNDRED
        Return value:
        - voltage : measurement voltage

        Exceptions: 
        - ValueError
        - VisaIOErrorTimeout
        """
        # Check for valid channel and range
        if ((   
                slot != self.daqm901a_1 and
                slot != self.daqm901a_2
            ) 
            or 
            (
                voltage_range!=RANGE_VOLT_MILLI and 
                voltage_range!=RANGE_VOLT_ONE and 
                voltage_range!=RANGE_VOLT_TEN and
                voltage_range!=RANGE_VOLT_HUNDRED and
                voltage_range!=RANGE_VOLT_THREE_HUNDRED
            )
            or channel<1
            or channel>20
            ):
                raise ValueError("Wrong input parameter for function: measure_voltage_dc\nUse correct slot, channel and voltage range!")

        command = f"MEASure:VOLTage:DC? {voltage_range},MAX,(@{slot:01d}{channel:02d})"
        return float(self.instrument.query(command))
            

    def measure_voltage_ripple(self, slot: int, channel: int):
        """
        This function returns the max measured AC ripple voltage on the selected channel on one of the DAQM901A multiplexers.

        Input parameters:
        - slot : the slot number where the DAQM901A module is inserted, should be DAQM01A_1_SLOT or DAQM01A_2_SLOT.
        - channel : selected channel number (1-20)

        Return value:
        - voltage : measurement voltage, peak to peak ripple

        Exceptions: 
        - ValueError
        - VisaIOErrorTimeout
        """
        # Check for valid channel and range
        if ((   
                slot != self.daqm901a_1 and
                slot != self.daqm901a_2
            )
            or channel<1
            or channel>20
            ):
                raise ValueError("Wrong input parameter for function: measure_voltage_ripple\nUse correct slot and channel")

        command = f"CONF:VOLT:DC AUTO,MAX,(@{slot:01d}{channel:02d})"
        self.instrument.write(command)
        command = f"SAMPle:TIMer MIN"
        self.instrument.write(command)
        command = f"SAMPle:COUNt 100"
        self.instrument.write(command)
        command = f"TRIGger:SOURce TIMer"
        self.instrument.write(command)
        command = f"TRIGger:COUNt 50"
        self.instrument.write(command)
        command = f"TRIGger:DELay MIN"
        self.instrument.write(command)
        command = f"TRIGger:TIMer MIN"
        self.instrument.write(command)
        command = f"ROUTe:SCAN (@{slot:01d}{channel:02d})"
        self.instrument.write(command)
        command = f"INIT"
        self.instrument.write(command)
        command = f"STATus:OPERation:CONDition?"
        wait = True
        while wait:
            measurement = self.instrument.query(command)
            wait = int(measurement)&16 #Check if scan is running
            time.sleep(0.5)
        command = f"CALCulate:AVERage:PTPeak? (@{slot:01d}{channel:02d})"
        peak = self.instrument.query(command)
        command = f"ROUTe:SCAN (@)"
        self.instrument.write(command)
        return float(peak)

    def measure_avg_resistance(self, slot: int, channel: int, resistance_range: int):
        """
        This function returns the average measured resistance on the selected channel on one of the DAQM901A multiplexers.

        Input parameters:
        - slot : the slot number where the DAQM901A module is inserted, should be DAQM01A_1_SLOT or DAQM01A_2_SLOT.
        - channel : selected channel number (1-20)
        - resistance_range : the range of the expected resistance. For the details of the constants see the comments above!
            possible resistance_range values: RANGE_OHM_HUNDRED, RANGE_KOHM_ONE, RANGE_KOHM_TEN, RANGE_KOHM_HUNDRED, 
                                              RANGE_MOHM_ONE, RANGE_MOHM_TEN, RANGE_MOHM_HUNDRED, RANGE_GOHM_ONE
        Return value:
        - resistance : measured avg resistance

        Exceptions: 
        - ValueError
        - VisaIOErrorTimeout

        """
        if ((   
                slot != self.daqm901a_1 and
                slot != self.daqm901a_2
            ) 
            or 
            (
                resistance_range!=RANGE_OHM_HUNDRED and 
                resistance_range!=RANGE_KOHM_ONE and 
                resistance_range!=RANGE_KOHM_TEN and
                resistance_range!=RANGE_KOHM_HUNDRED and
                resistance_range!=RANGE_MOHM_ONE and
                resistance_range!=RANGE_MOHM_TEN and
                resistance_range!=RANGE_MOHM_HUNDRED and
                resistance_range!=RANGE_GOHM_ONE

            )
            or channel<1
            or channel>20
            ):
                raise ValueError("Wrong input parameter for function: measure_resistance\nUse correct slot, channel and resistance range!")
        command = f"CONF:RES {resistance_range},MAX,(@{slot:01d}{channel:02d})"
        self.instrument.write(command)
        command = f"SAMPle:TIMer MIN"
        self.instrument.write(command)
        command = f"SAMPle:COUNt 50"
        self.instrument.write(command)
        command = f"TRIGger:SOURce TIMer"
        self.instrument.write(command)
        command = f"TRIGger:COUNt 20"
        self.instrument.write(command)
        command = f"TRIGger:DELay MIN"
        self.instrument.write(command)
        command = f"TRIGger:TIMer MIN"
        self.instrument.write(command)
        command = f"ROUTe:SCAN (@{slot:01d}{channel:02d})"
        self.instrument.write(command)
        command = f"INIT"
        self.instrument.write(command)
        command = f"STATus:OPERation:CONDition?"
        wait = True
        while wait:
            measurement = self.instrument.query(command)
            wait = int(measurement)&16 #Check if scan is running
            time.sleep(0.5)
        command = f"CALCulate:AVERage:AVERage? (@{slot:01d}{channel:02d})"
        avg = self.instrument.query(command)
        command = f"ROUTe:SCAN (@)"
        self.instrument.write(command)
        return float(avg)

    def measure_resistance(self, slot: int, channel: int, resistance_range: int):
        """
        This function returns the measured resistance on the selected channel on one of the DAQM901A multiplexers.

        Input parameters:
        - slot : the slot number where the DAQM901A module is inserted, should be DAQM01A_1_SLOT or DAQM01A_2_SLOT.
        - channel : selected channel number (1-20)
        - resistance_range : the range of the expected resistance. For the details of the constants see the comments above!
            possible resistance_range values: RANGE_OHM_HUNDRED, RANGE_KOHM_ONE, RANGE_KOHM_TEN, RANGE_KOHM_HUNDRED, 
                                              RANGE_MOHM_ONE, RANGE_MOHM_TEN, RANGE_MOHM_HUNDRED, RANGE_GOHM_ONE
        Return value:
        - resistance : measurement resistance

        Exceptions: 
        - ValueError
        - VisaIOErrorTimeout

        """
        if ((   
                slot != self.daqm901a_1 and
                slot != self.daqm901a_2
            ) 
            or 
            (
                resistance_range!=RANGE_OHM_HUNDRED and 
                resistance_range!=RANGE_KOHM_ONE and 
                resistance_range!=RANGE_KOHM_TEN and
                resistance_range!=RANGE_KOHM_HUNDRED and
                resistance_range!=RANGE_MOHM_ONE and
                resistance_range!=RANGE_MOHM_TEN and
                resistance_range!=RANGE_MOHM_HUNDRED and
                resistance_range!=RANGE_GOHM_ONE

            )
            or channel<1
            or channel>20
            ):
                raise ValueError("Wrong input parameter for function: measure_resistance\nUse correct slot, channel and resistance range!")
        command = f"MEASure:RESistance? {resistance_range},MAX,(@{slot:01d}{channel:02d})"
        return float(self.instrument.query(command))
            

    def set_channel_bits(self, channel: int, bits: int):
        """
        This function sets the output bits of the DAQM907A selected channel.

        Input parameters:
        - channel : selected channel number (1-2)
        - bits : 8-bit number to be output (0-255)

        Exceptions: 
        - ValueError
        - VisaIOErrorTimeout
        """
        if (channel<1 or channel>2 or bits<0 or bits>255):
                raise ValueError("Wrong input parameter for function: set_channel_bits\nUse correct channel and bit range!")
        command = f"SOURce:DIGital:DATA:BYTE {bits}, (@{self.daqm907a:01d}{channel:02d})"
        self.instrument.write(command)

    def query_channel_state(self, channel: int):
        """
        This function returns the state of the selected digital I/O channel.

        Input parameters:
        - channel : selected channel number(1-2)

        Return value:
        - io_state : state of the I/O channel (Output, Input)

        Exceptions: 
        - ValueError
        - VisaIOErrorTimeout
        """
        if (channel<1 or channel>2):
                raise ValueError("Wrong input parameter for function: query_channel_state\nUse correct channel range!")
        command = f"SOURce:DIGital:STATe? (@{self.daqm907a:01d}{channel:02d})"
        state = self.instrument.query_ascii_values(command)
        if state:
            return "Output"
        return "Input"

    def reset(self):
        command = "*RST"
        self.instrument.write(command)
        self.set_channel_bits(1,255)
        self.set_channel_bits(2,255)

    def query_channel_bits(self, channel):
        if (channel<1 or channel>2):
                raise ValueError("Wrong input parameter for function: query_channel_bits\nUse correct channel range!")
        command = f"SOURce:DIGital:DATA:BYTE? (@{self.daqm907a:01d}{channel:02d})"
        return int(self.instrument.query(command))

    def display_text(self, text: str):
        """
        This function displays the given text on the display of the DAQ973A

        Input parameters:
        - text : Text to be displayed
        """
        command = f"DISPlay:TEXT \"{text}\""
        self.instrument.write(command)
    def display_clear(self):
        """
        This function clears the display of the DAQ973A
        """
        command = f"DISPlay:TEXT:CLEar"
        self.instrument.write(command)

    def display_turn_on_off(self,turn_on:bool):
        """
        This function turns the display of the DAQ973A on/off

        Input parameters:
        - turn_on : True to turn on False to turn off
        """
        state = "ON" if turn_on else "OFF"
        command = f"DISPlay {state}"
        self.instrument.write(command)


# Example usage
if __name__ == "__main__":
#     # Instantiate the wrapper class with the instrument's VISA address
    daq973a = DAQM973A()


    daq973a.display_text("HYAAA")


    # print(daq973a.measure_voltage_ripple(DAQM901A_1_SLOT,2))
    # print(daq973a.measure_voltage_dc(DAQM901A_1_SLOT,2,RANGE_VOLT_TEN))
    # for i in range(1,256):
    #     print(f"{i}:")
    #     print(daq973a.set_channel_bits(2,i))
    #     time.sleep(1)
    # Perform a voltage measurement on channel 7
    # daqm901a_channel = 7
    # slot = DAQM901A_1_SLOT
    

    #Perform a write to the first digital I/O channel
    write_value = 0x5F
    daqm907a_channel = 1
    resp = daq973a.set_channel_bits(daqm907a_channel, write_value) 
    if resp != 0:
        print("Write succesful")
    else:
        print("Write failed")
