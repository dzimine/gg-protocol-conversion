# ModbusToAWSIoT.py
# This is an example script that connects to a modbus slave device to read
# a temperature value and publish to an MQTT Topic in AWS IoT every few seconds.
# If an exception occurs, it will wait few seconds and try again.

# import platform
# from threading import Timer
import time
import datetime
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


log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

HOST = os.environ.get('HOST', '127.0.0.1')
# Default port for modbus slave is typically 502. Using 5020 for simulation to avoid root permissions.
PORT = os.environ.get('PORT', 5020)
POLL_INTERVAL = os.environ.get('POLL_INTERVAL', 5)

log.info("Initializing modbus client: {0}:{1}".format(HOST, PORT))
mbclient = ModbusClient(HOST, port=PORT)

log.info("Initializing greengrass SDK client...")
client = greengrasssdk.client('iot-data')


# This procedure will poll the bearing temperature from a
# modbus slave device (simulator) and publish the value to AWS IoT via MQTT.
def poll_device():
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
                'humdity': decoder.decode_32bit_float(),
                'light': decoder.decode_8bit_int(),
                'temp': decoder.decode_32bit_float()
            }
            log.info("Value decoded: {0}".format(decoded))

            decoded['time'] = str(datetime.datetime.now())
            decoded['@timestamp'] = int(time.time())

            log.info("Publish results to topic in AWS IoT...")
            client.publish(topic='dt/controller/plc1/rtd', payload=json.dumps(decoded))
        except Exception as e:
            logging.info("Error: {0}".format(str(e)))
            client.publish(topic='dt/controller/errors', payload=json.dumps({'Error': str(e)}))

        time.sleep(POLL_INTERVAL)

poll_device()


# This is a dummy handler and will not be invoked on GG
def handler(event, context):
    return
