import time
import serial
from socket import socket as sckt, AF_INET, SOCK_STREAM
from config import (
    CV180_IP,
    CV180_PORT,
    T12S_IP,
    T12S_PORT,
    cv180_connection_error,
    cv180_communication_error,
    CV180_connection_timeout,
    TIMEOUT_SERIAL,
    BAUDRATE_SERIAL,
    #RS232_PORT,
    #RS485_PORT
)
import re


class CV180:
    socket: sckt
    connected: bool
    connection_timeout: bool

    def __init__(self, connect: bool, t12s: bool):
        if connect:
            time.sleep(60) #wait for boot to finish
            self.connect(t12s)
        else:
            self.connected = False

    def __del__(self):
        if self.connected:
            print("CLOSE CV180 CONNECTION")
            self.socket.close()

    def disconnect(self):
        self.socket.close()

    def connect(self, t12s):
        # init variables
        begin = time.time()
        self.connected = False

        while 1:
            # if timeout expired or connection was successful
            if self.connected or time.time() - begin > CV180_connection_timeout:
                print("Time: ", time.time(),   begin)
                if not (self.connected):
                    self.connection_timeout = True
                break

            try:
                # connect
                self.socket = sckt(AF_INET, SOCK_STREAM)
                if(t12s):
                    self.socket.connect((T12S_IP, T12S_PORT))
                    # set test user
                    result, error = self.send_and_receive("user=devu")
                else:
                    print('8XG ')
                    self.socket.connect((CV180_IP, CV180_PORT))
                    print('CV180_ip', CV180_IP)
                    # set test user
                    result, error = self.send_and_receive("user=testu")

                # check error and result
                print("Connecting...", result, error)
                if error:
                    # or 'EoLT TEST\r\n' != result:
                    print("error")
                    self.connected = False
                else:
                    if result and result.strip() == "EoLT TEST" or result.strip() == "Development":
                        self.connected = True
                        print("success")
                    else:
                        self.connected = False
            except:
                print("except")
                self.connected = False

            # wait 1s
            time.sleep(1)

    def send_and_receive(self, message: str, timeout = 0.1):
        # returns: result, error
        try:
            self.socket.send(bytes(f"{message}\r\n\r\n", "utf-8"))
            resp, error = self.__recv_timeout(timeout)

            if error:
                return None, {
                    "status": cv180_communication_error,
                    "error": "Connection broke with CV180",
                }
            return resp, None
        except:
            return None, {
                "status": cv180_communication_error,
                "error": "Failed to communicate with the CV180",
            }

    def send_only(self, message: str):
        # returns: result, error
        resp = 0
        try:
            resp = self.socket.send(bytes(f"{message}\r\n\r\n", "utf-8"))
            return resp, None
        except:
            return None, {
                "status": cv180_communication_error,
                "error": "Failed to communicate with the CV180",
            }

    def receive_only(self):
        # returns: result, error
        try:
            #print('belement')
            resp = self.socket.recv(8192)
            #print('kiment')

            #if error:
            #    return None, {
            #        "status": cv180_communication_error,
            #        "error": "ITT tort el Connection broke with CV180 ",
            #    }
            return resp, None
        except:
            print("Geba")
            return None, {
                "status": cv180_communication_error,
                "error": "Failed to communicate with the CV180",
            }

    def send_and_receive_serial(self, com: str, message: str):
        ser = serial
        print("Trying to connect to " + com)
        # returns: result, error
        try:
            # connect to serial port
            try:
                ser = serial.Serial(com, BAUDRATE_SERIAL, timeout=TIMEOUT_SERIAL)     # Connect to serial port
                print("Serial port opened successfully")
            except serial.SerialException as e:
                print(f"Error: {str(e)}")

            # check error and result
            if str(com) not in str(ser):
                print("Error by opening serial port " + com)
                return None, {
                    "status": cv180_communication_error,
                    "error": f'Unable to connect to {com}',
                }
        except:
            print("except")
            return None, {
                "status": cv180_communication_error,
                "error": f'Unable to connect to {com}',
            }

        # Send message to the DUT
        resp = ser.write(bytes(f"{message}\r\n", "utf-8"))
        if resp <= 0:
            return None, {
                "status": cv180_communication_error,
                "error": f'Message could not be sent via the serial port {com}!',
            }

        # Wait a little for the response
        time.sleep(0.5)
        # Get response from the DUT
        resp = ser.readline()
        # Disconnect from the serial port
        ser.close()

        if "Success" not in str(resp):
            return None, {
                "status": cv180_communication_error,
                "error": f'Response could not be received via the serial port {com}!',
            }
        
        # Return with the response
        return str(resp), None

    def receive_and_send_serial(self, com: str, expected: str, response: str, intmod_cmd: str):
        ser = serial
        
        # returns: result, error
        try:
            # connect to serial port
            try:
                ser = serial.Serial(com, BAUDRATE_SERIAL, timeout=TIMEOUT_SERIAL)     # Connect to serial port
                print("Serial port opened successfully", str(ser))
            except serial.SerialException as e:
                print(f"Error: {str(e)}")

            # check error and result
            if str(com) not in str(ser):
                print("Error by opening serial port " + com)
                # Disconnect from the serial port
                ser.close()
                return None, {
                    "status": cv180_communication_error,
                    "error": f'Unable to connect to {com}',
                }

        except:
            print("except")
            # Disconnect from the serial port
            ser.close()
            return None, {
                "status": cv180_communication_error,
                "error": f'Unable to connect to {com}',
            }

        self.send_only(intmod_cmd)
        # Check if received something from the DUT
        # Wait a little for the response
        time.sleep(0.5)
        # Get response from the DUT
        resp = ser.readline()
        
        print("Resp send only utan : ", str(resp))
        print("EXPECTED:    ", expected)

        if str(expected) not in str(resp):
            # Disconnect from the serial port
            ser.close()
            return None, {
                "status": cv180_communication_error,
                "error": f'Message is different as expected!',
            }

        # Send the response to the DUT
        resp = ser.write(bytes(f"{response}\r\n", "utf-8"))
        print("Resp after sending resp to DUT:   ", resp)
        # Wait a little
        time.sleep(0.5)
        # Disconnect from the serial port
        ser.close()
        # Check if response was sent
        if resp <= 0:
            # Disconnect from the serial port
            ser.close()
            return None, {
                "status": cv180_communication_error,
                "error": f'Response could not be sent via the serial port {com}!',
            }
        # Return with the response
        return resp, None

    def __recv_timeout(self, timeout=0.1):
        # returns: result, error
        # make socket non blocking
        self.socket.setblocking(0)

        # timeout error flag
        error = False

        # total data partwise in an array
        total_data = []
        data = ""

        # beginning time
        begin = time.time()
        while 1:
            # if you got some data, then break after timeout
            if total_data and time.time() - begin > timeout:
                break

            # if you got no data at all, wait a little longer, twice the timeout
            elif time.time() - begin > timeout * 2:
                error = True
                break

            # recv something
            try:
                data = self.socket.recv(8192)
                if data:
                    total_data.append(data)
                    # change the beginning time for measurement
                    begin = time.time()
                else:
                    # sleep for sometime to indicate a gap
                    time.sleep(0.1)
            except:
                pass

        # join all parts to make final string
        response = ""

        for i in total_data:
            response += i.decode()

        # cut \n down
        response = response.strip()

        return response, error


def sterilize_cv180_response(command: str, text: str):
    # command: |Q|Test(TestDCHeatOverCurrentHS), |Q|Test(TestDCHeatCurrentHS)
    # text:    |Q|TestDCHeatOverCurrentHS(Connected) |Q|TestDCHeatCurrentHS(-0.22A)

    command = command.replace("|Q|Test(", "")
    command = command.replace(")", "")
    text = text.replace(f"|Q|{command}(", "")
    text = text.replace(")", "")

    # -2.4343A
    pattern = r"-?\d+\.\d+|-?\d+"
    reg_res = re.search(pattern, text)
    if reg_res:
        text = reg_res.group()
        if "." in text:
            return float(text)
        else:
            return int(text)
    else:
        return text

def sterilize_response(command: str, text: str, i: int):
    # Extract the relevant part from the command
    command_prefix = "@PC;T12S_"
    if command.startswith(command_prefix):
        command = command[len(command_prefix):]
    
    # Extract the relevant part from the text
    text_prefix = "100013400-"
    if text.startswith(text_prefix):
        text = text[len(text_prefix):]

    # Use a regular expression to extract the numeric value
    pattern = r"-?\d+\.\d+|-?\d+"
    reg_res = re.search(pattern, text)
    
    if reg_res:
        text = reg_res.group()
        if "." in text:
            return "100013400-" + str(float(text) * i)
        else:
            return "100013400-" + str(int(text) * i)
    else:
        return "100013400-" + str(i * 1111)


if __name__ == "__main__":
    c = CV180(True)
    """ r, e = c.send_and_receive('heater=0')

    print(r, e)  """
    command = "|Q|Test(TestDCHeatOverCurrentLS)"
    r, e = c.send_and_receive(command)
    r = sterilize_cv180_response(command, r)
    print(r)


# this version sucks
""" class CV180():
    socket: sckt
    connected: bool

    def __init__(self) -> None:
        self.connected = False

    def __del__(self): 
        if self.connected:
            print('CLOSE CV180 CONNECTION')
            self.socket.close() 

    def connect(self):
        try:
            # connect
            self.socket = sckt(AF_INET, SOCK_STREAM)
            self.socket.connect((CV180_IP, CV180_PORT))
            
            self.connected = True

            # set test user
            result, error = self.send_and_receive('user=testu') 
            if not error and 'EoLT TEST\r\n' != result:
                self.connected = False

        except:
            self.connected = False

    def send_and_receive(self, message: str):# -> ( str | None, dict | None ):
        if not self.connected:
            self.connect()
            if not self.connected:
                return None, { "status": cv180_connection_error, "error": "Failed to connect to the CV180" }
        try:
            
            ready_to_read, ready_to_write, in_error = \
                select.select([self.socket,], [self.socket,], [], 5)
            print(ready_to_read, ready_to_write, in_error)
            except select.error:
                self.socket.close()
                # connection error event here, maybe reconnect
                print('connection error')
            self.socket.send(bytes(f'{message}\r\n\r\n', 'utf-8'))
            return self.__recv_timeout(), None
        except ConnectionAbortedError as e:
            print("MEGVAN")
            return None, { "status": cv180_communication_error, "error": "elkaptam" }
        except:
            return None, { "status": cv180_communication_error, "error": "Failed to communicate with the CV180" }
        


    def __recv_timeout(self, timeout=0.1) -> str:
        # make socket non blocking
        self.socket.setblocking(0)
        
        # total data partwise in an array
        total_data=[]
        data=''
        
        # beginning time
        begin=time.time()
        while 1:
            # if you got some data, then break after timeout
            if total_data and time.time()-begin > timeout:
                break
            
            # if you got no data at all, wait a little longer, twice the timeout
            elif time.time()-begin > timeout*2:
                break
            
            # recv something
            try:
                data = self.socket.recv(8192)
                if data:
                    total_data.append(data)
                    # change the beginning time for measurement
                    begin=time.time()
                else:
                    # sleep for sometime to indicate a gap
                    time.sleep(0.1)
            except:
                pass
        
        # join all parts to make final string
        response = ''
        for i in total_data:
            response += i.decode()
            
        return response

# example usage
if __name__ == '__main__':

    ip_address = '10.23.0.50'
    port = 1231

    cv180 = CV180()
    
    print(cv180.send_and_receive('|Q|Test(TestDCHeatDetect)')) """
