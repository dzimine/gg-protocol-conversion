#
# Reads the registry from modbus slave device
#

import logging
import sys
import json

from pymodbus.client.sync import ModbusTcpClient as ModbusClient

HOST = '127.0.0.1'
PORT = 5020

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

mbclient = ModbusClient('127.0.0.1', port=5020)


# Get the values from a modbus slave device (simulator)
# TODO: Reading different data types (e.g. 32bit_float)
def get_value():

    # Syntaxic sugar to get registers off the blocks
    #
    addr_from = 0

    def get(register):
        return rr.registers[register - addr_from]

    try:
        # Read a continious block of registers [from...to], parse out the values
        addr_from = 1202
        count = 10
        rr = mbclient.read_holding_registers(addr_from, count, unit=1)
        d = {
            'frequency': get(1202),
            'current': get(1204),
            'torque': get(1205),
            'voltage': get(1208),
            'power': get(1211)
        }

        # Read a continious block of registers [from...to], parse out the values
        addr_from = 2004
        count = 9
        rr = mbclient.read_holding_registers(addr_from, count, unit=1)
        d['speed_SPD'] = get(2004)
        d['speed_SPDM'] = get(2011)
        d['speed_SPD1'] = get(2012)

        # Compute the power
        d['power_computed'] = d['torque'] * (d['speed_SPD'] / 5252.0)

        logging.info("Value decoded: {0}".format(json.dumps(d, indent=4)))
    except Exception, e:
        logging.info("Error: {0}".format(str(e)))

get_value()
