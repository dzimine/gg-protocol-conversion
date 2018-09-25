# This is a simulator script that connects to a modbus slave device and
# writes the CPU temperature for the raspberry pi device to a modbus register.
# If an exception occurs, it will wait 5 seconds and try again.

import time
import logging
import sys
import random

from pymodbus.client.sync import ModbusTcpClient as ModbusClient
# from pymodbus.payload import BinaryPayloadDecoder
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


def get_temp():
    CPUTemp = random.random()
    return float(CPUTemp)


# in an infinite loop, this procedure will poll the cpu temperature and write
# it to a local modbus slave device.
def poll_temp():
    while True:
        try:
            client.connect()
            builder = BinaryPayloadBuilder(wordorder=Endian.Big)
            temp = get_temp()
            builder.add_32bit_float(temp)
            payload = builder.build()
            address = 0
            rq = client.write_registers(address, payload, skip_encode=True, unit=1)
            logging.info("wrote temp {0} to registers: {1}".format(temp, str(payload)))

        except Exception as e:
            logging.info("Error: {0}".format(str(e)))

        time.sleep(5)

# executing polling on startup.
poll_temp()
