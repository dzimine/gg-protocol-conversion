# This is a simulator script that connects to a modbus slave device and
# writes the CPU temperature for the raspberry pi device to a modbus register.
# If an exception occurs, it will wait 5 seconds and try again.

import time
import logging
import sys
import random

from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian
# from pymodbus.compat import iteritems

# Default port for modbus slave is typically 502. Using 5020 for simulation to
# avoid root permissions.
client = ModbusClient('127.0.0.1', port=5020)

# instantiate logger which will log any exceptions to Cloudwatch or Greengrass
# local logs
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_decoder(typename, bits):
    name = "decode_{0}bit_{1}".format(bits, typename)
    return lambda d: getattr(d, name)()


def get_builder(typename, bits):
    name = "add_{0}bit_{1}".format(bits, typename)
    return lambda d: getattr(d, name)


def build_payload():
    '''
    Simulate the following payload:
      1. humdity - float32 (eg 45.3 %)
      2. light - uint (0 or 1)
      3. temp float32 (eg 21.3 C)

    '''
    state = [
        {
            'displayName': 'humidity',
            'type': 'float',
            'bits': 32,
            'value': float(random.random())
        },
        {
            'displayName': 'light',
            'type': 'uint',
            'bits': 8,
            'value': int(random.choice([0, 1]))
        },
        {
            'displayName': 'temp',
            'type': 'float',
            'bits': 32,
            'value': float(random.random())
        }

    ]

    builder = BinaryPayloadBuilder(wordorder=Endian.Big)

    values = []
    for s in state:
        values.append("{0} = {1};".format(s['displayName'], s['value']))
        get_builder(s['type'], s['bits'])(builder)(s['value'])

    logging.info("Writing values: " + "".join(values))

    return builder.build()


# in an infinite loop, this procedure will poll the cpu temperature and write
# it to a local modbus slave device.
def poll_temp():
    while True:
        try:
            client.connect()
            address = 0
            payload = build_payload()
            client.write_registers(address, payload, skip_encode=True, unit=1)
            logging.info("Wrote to holding registers: {0}".format(str(payload)))

        except Exception as e:
            logging.info("Error: {0}".format(str(e)))

        time.sleep(5)

# executing polling on startup.
poll_temp()
