#
# Runs a modbus slave device in memory for testing purposes.
# It allocates registers for the modbus tcp slave and starts
# the server. If an exception occurs, it will wait 5 seconds and try again.


import time
import logging
import sys

from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

# instantiate logger which will log any exceptions to Cloudwatch or Greengrass
# local logs
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

while True:
    try:
        # create registy for modbus server
        store = ModbusSlaveContext(
            co=ModbusSequentialDataBlock(0, [11] * 100),
            di=ModbusSequentialDataBlock(0, [12] * 100),
            hr=ModbusSequentialDataBlock(0, [13] * 100),
            ir=ModbusSequentialDataBlock(0, [14] * 100))
        context = ModbusServerContext(slaves=store, single=True)

        # change default port of modbus from 502 to 5020 as it requires
        # root permissions below 1024
        logging.info("Serving modbus at localhost:5020...")
        StartTcpServer(context, address=("localhost", 5020))
    except Exception, e:
        logging.info("Error: {0}".format(str(e)))
    time.sleep(5)
