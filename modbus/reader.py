#
# Reads the registry from modbus slave device
#

import logging
import sys
import json

from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

HOST = '127.0.0.1'
PORT = 5020
UNIT = 1

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

mbclient = ModbusClient(HOST, port=PORT)


class RegistryReader(object):

    def __init__(self, addr_from, addr_to, registers):
        self._from = addr_from
        self._to = addr_to
        self._registers = registers
        self.byteorder = Endian.Big
        self.wordorder = Endian.Little

    @classmethod
    def readBlock(klass, addr_from, addr_to, unit):

        rr = mbclient.read_holding_registers(addr_from, addr_to - addr_from + 2, unit=unit)
        return klass(addr_from, addr_to, rr.registers)

    def read(self, addr):
        return self._registers[addr - self._from]

    def read_encoded(self, addr, type, bits):
        idx_from = addr - self._from
        registers = self._registers[idx_from: idx_from + (8 * bits)]
        d = BinaryPayloadDecoder.fromRegisters(registers, wordorder=Endian.Big)
        method_name = "decode_{0}bit_{1}".format(bits, type)
        return getattr(d, method_name)()


# Get the values from a modbus slave device (simulator)
# TODO: Reading different data types (e.g. 32bit_float)
def get_value():

    reader = RegistryReader.readBlock(addr_from=1202, addr_to=1214, unit=UNIT)
    d = {
        'frequency': reader.read_encoded(1202, type='float', bits=32),
        'current': reader.read(1204),
        'torque': reader.read_encoded(1205, type='float', bits=32),
        'voltage': reader.read(1208),
        'power': reader.read(1211)
    }

    logging.info("Value decoded: {0}".format(json.dumps(d, indent=4)))

    # Read a continious block of registers [from...to], parse out the values
    reader = RegistryReader.readBlock(addr_from=2004, addr_to=2012, unit=UNIT)

    d['speed_SPD'] = reader.read_encoded(2004, type='float', bits=32)
    d['speed_SPDM'] = reader.read(2011)
    d['speed_SPD1'] = reader.read(2012)

    # Compute the power
    d['power_computed'] = d['torque'] * (d['speed_SPD'] / 5252.0)

    logging.info("Value decoded: {0}".format(json.dumps(d, indent=4)))

get_value()
