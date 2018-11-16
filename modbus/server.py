#
# Runs a modbus slave device in memory for testing purposes.
# It allocates registers for the modbus tcp slave and starts

import logging
import sys

from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

HOST = '0.0.0.0'
PORT = 5020

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

try:
    # create registy for modbus server
    store = ModbusSlaveContext(
        co=ModbusSequentialDataBlock(0, [11] * 100),
        di=ModbusSequentialDataBlock(0, [12] * 100),
        hr=ModbusSequentialDataBlock(3000, [13] * 10000),
        ir=ModbusSequentialDataBlock(0, [14] * 100)
    )

    context = ModbusServerContext(slaves=store, single=True)

    logging.info("Serving modbus at {0}:{1}...".format(HOST, PORT))
    StartTcpServer(context, address=(HOST, PORT))
except Exception as e:
    logging.info("Error: {0}".format(str(e)))
