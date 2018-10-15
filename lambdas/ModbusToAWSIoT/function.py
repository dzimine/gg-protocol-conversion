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

HOSTS = os.environ.get('HOSTS', '127.0.0.1:5020, localhost:5020')
PORT = os.environ.get('PORT', 5020)
POLL_INTERVAL = os.environ.get('POLL_INTERVAL', 5)
UNIT = 1


class RegistryReader(object):
    '''
    Convinient reader for holding registers, including endoced variables.
    '''

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
        # TODO: support `read_bytes` and `read_string`.
        idx_from = addr - self._from
        registers = self._registers[idx_from: idx_from + (8 * bits)]
        d = BinaryPayloadDecoder.fromRegisters(registers, wordorder=Endian.Big)
        method_name = "decode_{0}bit_{1}".format(bits, type)
        return getattr(d, method_name)()


def get_modbus_clients(hostlist):
    mb_clients = []
    try:
        hosts = [h.strip() for h in hostlist.split(',')]
        for h in hosts:
            addr = h.split(':')
            host = addr[0]
            port = int(addr[1]) if len(addr) > 1 else 502
            log.info("Initializing modbus client: {0}:{1}".format(host, port))
            mb_clients.append(ModbusClient(host, port=port))
    except Exception as e:
        logging.info("Error while parsing host list '{0}': {1}".format(hostlist, str(e)))
        raise(e)
    return mb_clients


# This procedure will poll the bearing temperature from a
# modbus slave device (simulator) and publish the value to AWS IoT via MQTT.
def poll_device(mb_client, device_id, mqtt_client):
    try:
        log.info("Connecting to modbus slave device {0}:{0}".format(
            mb_client.host, mb_client.port))

        # Read a continious block of registers [from...to], parse out the values
        reader = RegistryReader.readBlock(mb_client, addr_from=1202, addr_to=1214, unit=UNIT)
        d = {
            'frequency': reader.read_encoded(1202, type='float', bits=32),
            'current': reader.read(1204),
            'torque': reader.read_encoded(1205, type='float', bits=32),
            'voltage': reader.read(1208),
            'power': reader.read(1211)
        }

        log.debug("Fisrt block decoded: {0}".format(json.dumps(d)))

        # Read a continious block of registers [from...to], parse out the values
        reader = RegistryReader.readBlock(mb_client, addr_from=2004, addr_to=2012, unit=UNIT)

        d['speed_SPD'] = reader.read_encoded(2004, type='float', bits=32)
        d['speed_SPDM'] = reader.read(2011)
        d['speed_SPD1'] = reader.read(2012)

        # Compute the power
        d['power_computed'] = d['torque'] * (d['speed_SPD'] / 5252.0)

        d['time'] = str(datetime.datetime.now())
        d['@timestamp'] = int(time.time())
        d['device_id'] = device_id

        log.info("Publish results to topic in AWS IoT...")
        mqtt_client.publish(
            topic='dt/control/{0}'.format(device_id),
            payload=json.dumps(d))
    except Exception as e:
        logging.info("Error: {0}".format(str(e)))
        mqtt_client.publish(
            topic='dt/errors/{0}'.format(device_id),
            payload=json.dumps({'Error': str(e)}))


log.info("Initializing greengrass SDK client...")
mqtt_client = greengrasssdk.client('iot-data')

mb_clients = get_modbus_clients(HOSTS)
log.debug("Modbus slaves: {0}".format(mb_clients))
# The NAIVE implementation would do for about a dozen of slaves.
# To scale for 30+ clients, re-implement as Async alient, e.g. with Twisted https://goo.gl/sDu5vc
while True:
    for i, mbc in enumerate(mb_clients):
        device_id = 'dev{0}'.format(i)
        poll_device(mbc, device_id, mqtt_client)
    time.sleep(POLL_INTERVAL)


# This is a dummy handler and will not be invoked on GG
def handler(event, context):
    return
