# This is a simulator script that connects to a modbus slave device and
# writes the CPU temperature for the raspberry pi device to a modbus register.
# If an exception occurs, it will wait 5 seconds and try again.

import time
import logging
import sys

from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian

HOST = '127.0.0.1'
PORT = 5020
UNIT = 1

# instantiate logger which will log any exceptions to Cloudwatch or Greengrass
# local logs
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def get_decoder(typename, bits):
    name = "decode_{0}bit_{1}".format(bits, typename)
    return lambda d: getattr(d, name)()


def get_builder(typename, bits):
    # returns a function pointing to a method of a typename
    # like add_16bit_int

    name = "add_{0}bit_{1}".format(bits, typename)
    return lambda d: getattr(d, name)


registers = [
    {
        'displayName': 'frequency',
        'address': 1202,
        'dtype': 'float',
        'bits': 32,
        'value': 1202.222
    },
    {
        'displayName': 'current',
        'address': 1204,
        'value': 1204.444
    },
    {
        'displayName': 'torque',
        'address': 1205,
        'value': 1205.555
    },
    {
        'displayName': 'voltage',
        'address': 1208,
        'value': 1208.888
    },
    {
        'displayName': 'power',
        'address': 1211,
        'value': 1211.111
    },
    {
        'displayName': 'speed_SPD',
        'address': 2004,
        'value': 2004.444
    },
    {
        'displayName': 'speed_SPDM',
        'address': 2011,
        'value': 2011.111
    },
    {
        'displayName': 'speed_SPD1',
        'address': 2012,
        'value': 1202.222
    },
    {
        'displayName': 'device_id',
        'address': 1012,
        'dtype': 'string',
        'value': 'dev0'
    },
]


class RegisterWriter():

    def __init__(self, host, port):
        self.mb_client = ModbusClient(host, port=port)
        self.mb_client.connect()

    def write(self, displayName, address, value, dtype=None, bits=None):
        if dtype:
            builder = BinaryPayloadBuilder(wordorder=Endian.Big)

            # This code trick generates and calls methods of PayloadBuilder,
            # like `builder.add_16bit_int(r['value'])
            # where 16 = r[bits], int = r['typename']
            if dtype == 'string':
                method_name = "add_string"
            else:
                method_name = "add_{0}bit_{1}".format(bits, dtype)
            getattr(builder, method_name)(value)

            payload = builder.build()

            logging.debug("Packed value '{0}' with method {1} into {2}".format(
                value, method_name, payload))

            self.mb_client.write_registers(address, payload, skip_encode=True, unit=UNIT)

        else:
            logging.debug("Wrote value '{0}' to 16bit register".format(value))
            self.mb_client.write_register(address, value, unit=UNIT)


# in an infinite loop, this procedure will poll the cpu temperature and write
# it to a local modbus slave device.
def poll_temp():
    writer = RegisterWriter(HOST, PORT)

    while True:
        try:
            for r in registers:
                writer.write(**r)

            logging.info("Wrote to holding registers: {0}".format(str(registers)))

        except Exception as e:
            logging.info("Error: {0}".format(str(e)))
            raise(e)

        time.sleep(5)

# executing polling on startup.
poll_temp()
