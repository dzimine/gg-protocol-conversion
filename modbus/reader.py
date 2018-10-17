#
# Reads the registry from modbus slave device
#

import logging
import sys
import json
from time import sleep
import datetime

from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

HOST = '127.0.0.1'
PORT = 5020
UNIT = 1
DEVICE_ID = 'dev_0'

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
    def readBlock(klass, mb_client, addr_from, addr_to, unit):

        rr = mb_client.read_holding_registers(addr_from, addr_to - addr_from + 2, unit=unit)
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
def get_value():

    reader = RegistryReader.readBlock(mbclient, addr_from=3202, addr_to=3236, unit=UNIT)
    d = {
        'frequency': reader.read(3202),
        'current': reader.read(3204),
        'torque': reader.read(3205),
        'voltage': reader.read(3208),
        'power': reader.read(3211),
        'torqueNm': reader.read(3216),
        'torquePercent': reader.read(3226)
    }

    logger.info("Value decoded: {0}".format(json.dumps(d, indent=4)))

    # Read a continious block of registers [from...to], parse out the values
    reader = RegistryReader.readBlock(mbclient, addr_from=12004, addr_to=12004, unit=UNIT)

    d['speed_SPD'] = reader.read(12004)

    # Compute the power
    d['power_computed'] = d['torque'] * (d['speed_SPD'] / 5252.0)

    d['device_id'] = DEVICE_ID

    logger.info("Value decoded: {0}".format(json.dumps(d, indent=4)))
    return d


if __name__ == '__main__':

    FILE = 'reads.json'
    N_RECORDS = 100
    INTERVAL = 5

    with open(FILE, 'w', buffering=1) as f:
        for i in range(1, N_RECORDS):
            d = get_value()
            d['time'] = str(datetime.datetime.now())
            f.write(json.dumps(d) + '\n')
            sleep(INTERVAL)
