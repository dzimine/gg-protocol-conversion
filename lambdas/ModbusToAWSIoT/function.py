# ModbusToAWSIoT.py
# This is an example script that connects to a modbus slave device to read
# a temperature value and publish to an MQTT Topic in AWS IoT every few seconds.
# If an exception occurs, it will wait few seconds and try again.

# import platform
# from threading import Timer
import time
import logging
import sys
import json
import os

# Import installed packages (in site-packages)
site_pkgs = os.path.join(os.path.dirname(os.path.realpath(__file__)), "site-packages")
sys.path.append(site_pkgs)

import greengrasssdk  # noqa

from pymodbus.client.sync import ModbusTcpClient as ModbusClient  # noqa
from pymodbus.payload import BinaryPayloadDecoder  # noqa
from pymodbus.constants import Endian  # noqa
from pymodbus.compat import iteritems  # noqa

# Instantiate the client for your modbus slave device. In this example we are
# using the local IP address where a simulator exists. Change this to your
# desired IP. In addition, the typical default port for Modbus TCP is 502. For
# this example, 5020 was used.


# Default port for modbus slave is typically 502. Using 5020 for simulation to
# avoid root permissions.
log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# TODO: use ENV
log.info("Initializing modbus client: {0}:{1}".format('127.0.0.1', 5020))
mbclient = ModbusClient('127.0.0.1', port=5020)

log.info("Initializing greengrass SDK client...")
client = greengrasssdk.client('iot-data')


# This procedure will poll the bearing temperature from a
# modbus slave device (simulator) and publish the value to AWS IoT via MQTT.
def poll_temp():
    while True:
        try:
            log.info("Connecting to modbus slave device...")
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
            log.info("Value decoded: {0}".format(decoded))

            log.info("Publish results to topic in AWS IoT...")
            for name, value in iteritems(decoded):
                client.publish(topic='dt/controller/plc1/rtd', payload=json.dumps({'Temp': value}))
        except Exception as e:
            logging.info("Error: {0}".format(str(e)))
            client.publish(topic='dt/controller/errors', payload=json.dumps({'Error': str(e)}))

        # TODO: use ENV
        time.sleep(5)

poll_temp()


# This is a dummy handler and will not be invoked on GG
def handler(event, context):
    return
