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

HOST = '127.0.0.1'
PORT = 5020
UNIT = 1
INTERVAL = 5

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
        'address': 3202,
        'value': '100 + random.uniform(-10, 10)'
    },
    {
        'displayName': 'current',
        'address': 3204,
        'value': '8 + random.uniform(-1, 1)'
    },
    {
        'displayName': 'torque',
        'address': 3205,
        'value': '73 + random.uniform(-3, 3)'
    },
    {
        'displayName': 'voltage',
        'address': 3208,
        'value': '40 + random.uniform(-2, 2)'
    },
    {
        'displayName': 'power',
        'address': 3211,
        'value': '1 + random.uniform(0, 1.2)'
    },
    {
        'displayName': 'torqueNm',
        'address': 3216,
        'value': 1
    },
    {
        'displayName': 'torquePercent',
        'address': 3226,
        'value': '300 + random.uniform(-30, 30)'
    },
    {
        'displayName': 'speed_SPD',
        'address': 12004,
        'value': '300 + random.uniform(-1.5, 1.5)'
    },
    {
        'displayName': 'device_id',
        'address': 3200,
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

            registers = builder.to_registers()
            self.mb_client.write_registers(address, registers, unit=1)
            # self.mb_client.write_registers(address, payload, skip_encode=True, unit=UNIT)

        else:
            logging.debug("Wrote value '{0}' to 16bit register".format(value))
            self.mb_client.write_register(address, value, unit=UNIT)


# in an infinite loop, this procedure will poll the cpu temperature and write
# it to a local modbus slave device.
def poll_temp():
    writer = RegisterWriter(HOST, PORT)

    random.seed()  # Shut up pyflakes "imported but unused"

    while True:
        try:
            written = []
            for r in registers:
                # Eval values to generate simulated data
                data = r.copy()
                if r.get('dtype') != 'string' and isinstance(r['value'], str):
                    data['value'] = eval(r['value'])

                writer.write(**data)

                written.append({data['displayName']: data['value']})

            logging.info("Wrote to holding registers: {0}".format(written))

        except Exception as e:
            logging.exception("Error: {0}".format(str(e)))

        time.sleep(INTERVAL)

poll_temp()
