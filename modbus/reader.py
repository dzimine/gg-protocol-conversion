# ModbusToAWSIoT.py
# This is an example script that connects to a modbus slave device to read
# a temperature value and publish to an MQTT Topic in AWS IoT every 5 seconds.
# If an exception occurs, it will wait 5 seconds and try again.
# Since the function is long-lived it will run forever when deployed to a
# Greengrass core.  The handler will NOT be invoked in our example since
# we are executing an infinite loop.

import time
import logging
import sys
import json

# import pymodbus libraries for the modbus client
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
# from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian
from pymodbus.compat import iteritems

# Instantiate the client for your modbus slave device. In this example we are
# using the local IP address where a simulator exists. Change this to your
# desired IP. In addition, the typical default port for Modbus TCP is 502. For
# this example, 5020 was used.
mbclient = ModbusClient('127.0.0.1', port=5020)

# Default port for modbus slave is typically 502. Using 5020 for simulation to
# avoid root permissions.
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


# Get the bearing value from a modbus slave device (simulator)
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
            'float': decoder.decode_32bit_float()
        }
        logging.info("Value decoded: {0}".format(decoded))
    except Exception, e:
        logging.info("Error: {0}".format(str(e)))

get_value()