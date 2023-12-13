import logging as log
import pyvisa
from config import RS_PSU_NAME, psu_channel_list, psu_reSet_values_error, psu_communication_error

""" _measured_protection = 'MEAS'
_protected_protection = 'PROT' """

# __init__ descitipton update


class hmp4040():
    rm: pyvisa.ResourceManager
    instrument: pyvisa.Resource
    channel_list: list
    connected: bool
    error: str

    def __init__(self):
        """ 
        This class implements a simple programming interface for the HMP4040 power supply. 
        
        Input parameters:
        - pyvisa_instr_name: eg. TCPIP::192.168.10.10::5025::SOCKET
        """
        self.rm = pyvisa.ResourceManager()
        self.connected = False
        try:
            self.instrument = self.rm.open_resource(RS_PSU_NAME)
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'
            self.connected = True
        except Exception as e:
            self.connected = False
            self.error = e
        self.channel_list = psu_channel_list
        

    def __del__(self):
        if self.connected:
            self.instrument.write('*RST')
            self.instrument.close()

    def __valid_channel(self, ch: int):
        """
        This private function returns whether the PSU has the given channel

        Input parameters:
        - ch : channel

        Return parameters:
        - valid_channel : 
            True: the channel exists
            False: the channel does not exist
        """
        return ch in self.channel_list

    def reset(self):
        # This function sets the power supply in default settings.
        self.instrument.write('*RST')

    
    def set_settings(self, settings: dict):
        """   description
        { 
            "out_gen": True,
            1: { "out": True, "voltage": DUT_VOLTAGE, "current": 0.1 },
            2: _channel_off,
            3: _channel_off,
            4: _channel_off
        } 
        """
        try:
            
            # if output general is off in settings it has to be turned off before setting other values
            if not settings["out_gen"]:
                self.instrument.write('OUTPut:GENeral:STATe 0')

            is_correct = True
            for channel in self.channel_list:
                if self.__valid_channel(channel):
                    channel_settings = settings[channel]
                    self.instrument.write('INSTrument:NSELect {0}'.format(channel))
                    
                    if not channel_settings["out"]:
                        self.instrument.write(f'OUTPut:SELect 0')

                    self.instrument.write(f'SOURce:VOLTage {channel_settings["voltage"]}')
                    self.instrument.write(f'SOURce:CURRent {channel_settings["current"]}')

                    if channel_settings["out"]:
                        self.instrument.write(f'OUTPut:SELect 1')
                    # check if values are correct
                    voltage          = float(self.instrument.query('SOURce:VOLTage?'))
                    current_lim      = float(self.instrument.query('SOURce:CURRent?'))
                    status           = bool(int(self.instrument.query('OUTPut:SELect?')))
                    
                    if voltage != channel_settings["voltage"] or current_lim != channel_settings["current"] or status is not channel_settings["out"]:
                        is_correct = False
            
            # if output general is on it has to be turned of after other values are set
            if settings["out_gen"]:
                self.instrument.write(f'OUTPut:GENeral:STATe 1')
            
            output_general = bool(int(self.instrument.query('OUTPut:GENeral:STATe?')))
            
            if not is_correct or output_general is not settings["out_gen"]:
                self.instrument.write('OUTPut:GENeral:STATe 0')
                return { "status": psu_reSet_values_error, "error": "The power supply could not set default settings"}
            return None # no error return -> success
        except Exception as e:
            return { "status": psu_communication_error, "error": e }
    
    def set_voltage(self, ch: int, voltage: float):
        """ 
        This function sets the output voltage of the power supply selected channel. 

        Input parameters:
        - ch: selected channel number (1-4)

        Return parameters:
            error: { status: error_status, error: message } OR None
        """
        try:
            self.instrument.write(f'INSTrument:NSELect {ch}')
            self.instrument.write(f'SOURce:VOLTage:LEVel:IMMediate:AMPlitude {voltage}')
            # check the channel and its voltage
            selected_channel = int(self.instrument.query(f'INSTrument:NSELect ?'))
            read_voltage = float(self.instrument.query(f'SOURce:VOLTage:LEVel:IMMediate:AMPlitude?'))
            # if the channel or the voltage is not set correctly
            if(not (ch == selected_channel and voltage == read_voltage)):
                return { "status": psu_reSet_values_error, "error": f"PSU could not set given voltage ({voltage}) on channel {ch}" }
            return None
        except:
            return { "status": psu_communication_error, "error": "Communication lost with the PSU."}

    def set_current(self, ch: int, current: float):
        """ 
        This function sets the output current of the power supply selected channel. 

        Input parameters:
        - ch: selected channel number (1-4)

        Return parameters:
            error: { status: error_status, error: message } OR None
        """
        self.instrument.write(f'INSTrument:NSELect {ch}')
        self.instrument.write(f'SOURce:CURRent:LEVel:IMMediate:AMPlitude {current}')
        # check the channel and its current
        selected_channel = int(self.instrument.query(f'INSTrument:NSELect ?'))
        read_current = float(self.instrument.query(f'SOURce:CURRent:LEVel:IMMediate:AMPlitude ?'))
        # if the channel or the current is not set correctly
        if(not (ch == selected_channel and current == read_current)):
            return { "status": psu_reSet_values_error, "error": f"PSU could not set given current ({current}) on channel {ch}" }
        return None

    def set_select(self, ch: int, state: int):
        """ 
        This function sets the output state of a channel.

        Input parameters:
        - ch: selected channel number (1-4)
        - state: activation state (0/1)
            - 1: activates the channel
            - 0: deactivates the channel
        """
        if self.__valid_channel(ch):
            self.instrument.write(f'INSTrument:NSELect {ch}')
            self.instrument.write(f'OUTPut:SELect {state}')
        return None
            


    def set_output_general(self, state: int):
        """ 
        This function sets or queries all previous selected channels simultaneously.

        Input parameters:
        - state: (0/1)
            - 0: Switches off previous selected channels simultaneously.
			- 1: Switches on previous selected channels simultaneously.
        """
        self.instrument.write(f'OUTPut:GENeral:STATe {state}')
        return None

    def get_voltage(self, ch: int):
        """ 
        This function returns the set voltage of the given channel.

        Input parameters:
        - ch: channel to read (1-4)

        Return value:
        - voltage: set voltage 
        """
        self.instrument.write(f'INSTrument:NSELect {ch}')
        return float(self.instrument.query('SOURce:VOLTage:LEVel:IMMediate:AMPlitude?'))

    def get_current(self, ch: int):
        """ 
        This function returns the set current of the given channel.

        Input parameters:
        - ch: channel to read

        Return value:
        - current: set current
        """
        self.instrument.write(f'INSTrument:NSELect {ch}')
        return float(self.instrument.query('SOURce:CURRent:LEVel:IMMediate:AMPlitude?'))

    def measure_voltage(self, ch: int):
        """ 
        This function returns the measured voltage of the seleted channel.

        Input parameters:
        - ch: channel to measure

        Return value:
        - voltage: measurement voltage 
        """
        self.instrument.write(f'INSTrument:NSELect {ch}')
        return float(self.instrument.query('MEASure:VOLTage?'))
    
    def measure_current(self, ch: int):
        """ 
        This function returns the current of the seleted channel.

        Input parameters:
        - ch: channel to measure

        Return value:
        - current: measurement current
        """
        self.instrument.write(f'INSTrument:NSELect {ch}')
        return float(self.instrument.query('MEASure:CURRent?'))

    #not used:
    """ def set_protection_mode(self, mode):
        
        #This fuction sets the protection mode on the PSU.

        #Input parameters:
        #- mode : ['MEAS' / 'PROT']
       
        if mode == _measured_protection or mode == _protected_protection:
            self.instrument.write(f'VOLT:PROT:MODE {mode}') 
        else:
            log.error('Protection mode not supported.')

    def set_voltage_protection(self, ch: int, voltage: float):
        
        #This function sets the voltage protection on the given channel of the power supply

        #Input parameters:
        #- ch : selected channel (1-4)
        #- voltage : voltage protecion number
       
        self.instrument.write(f'INSTrument:NSELect {ch}')
        self.instrument.write(f'VOLTage:PROTection {voltage}')  """


#Example
if __name__ == '__main__':
    insr_name = 'TCPIP::192.168.10.10::5025::SOCKET'
    
    hmp4040 = hmp4040(insr_name)
    
    #hmp4040.default_settings()

    #print(hmp4040.get_current(psu_dut))
