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

HOSTS = os.environ.get('HOSTS', '127.0.0.1:5020, 127.0.0.1:5020')
PORT = os.environ.get('PORT', 5020)
POLL_INTERVAL = os.environ.get('POLL_INTERVAL', 5)


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
        log.info("Connecting to modbus slave device...")
        # set the address and number of bytes that will be read on the modbus device
        address = 0x00
        count = 8
        # read the holding register value for the temperature
        rr = mb_client.read_holding_registers(address, count, unit=1)
        # decode results as a 32 bit float
        decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, wordorder=Endian.Big)
        decoded = {
            'humidity': decoder.decode_32bit_float(),
            'light': decoder.decode_8bit_int(),
            'temp': decoder.decode_32bit_float()
        }
        log.info("Value decoded: {0}".format(decoded))

        decoded['time'] = str(datetime.datetime.now())
        decoded['@timestamp'] = int(time.time())

        log.info("Publish results to topic in AWS IoT...")
        mqtt_client.publish(
            topic='dt/control/{0}'.format(device_id),
            payload=json.dumps(decoded))
    except Exception as e:
        logging.info("Error: {0}".format(str(e)))
        mqtt_client.publish(
            topic='dt/errors/{0}'.format(device_id),
            payload=json.dumps({'Error': str(e)}))


log.info("Initializing greengrass SDK client...")
mqtt_client = greengrasssdk.client('iot-data')

mb_clients = get_modbus_clients(HOSTS)
print mb_clients

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
