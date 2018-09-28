#
# Reads the registry from modbus slave device
#

import logging
import sys

# import pymodbus libraries for the modbus client
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
# from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian

# Instantiate the client for your modbus slave device. In this example we are
# using the local IP address where a simulator exists.
mbclient = ModbusClient('127.0.0.1', port=5020)

# Default port for modbus slave is typically 502. Using 5020 for simulation to
# avoid root permissions.
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


# Get the values from a modbus slave device (simulator)
def get_value():
    try:
        # connect to modbus slave device
        mbclient.connect()
        # set the address and number of bytes that will be read on the modbus device
        address = 0x00
        count = 8
        # read the holding register value for the temperature
        rr = mbclient.read_holding_registers(address, count, unit=1)
        # decode results as a 32 bit float
        decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, wordorder=Endian.Big)
        decoded = {
            'humdity': decoder.decode_32bit_float(),
            'light': decoder.decode_8bit_int(),
            'temp': decoder.decode_32bit_float()
        }
        logging.info("Value decoded: {0}".format(decoded))
    except Exception, e:
        logging.info("Error: {0}".format(str(e)))

get_value()
