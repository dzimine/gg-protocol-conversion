import os
import sys
import json

# Import installed packages (in site-packages)
site_pkgs = os.path.join(os.path.dirname(os.path.realpath(__file__)), "site-packages")
sys.path.append(site_pkgs)

import greengrasssdk  # noqa


# Creating a greengrass core sdk client
client = greengrasssdk.client('iot-data')


# Run Lambda as "lnog-running" (aka "pinned") to keep values in variables,
# yet it will respond to Subscription events.
counter = 0


def handler(event=None, context=None):
    '''
    Simulate anomaly by every 10th event
    '''
    global counter
    counter += 1
    print("counter={0}".format(counter))
    print(json.dumps(event))
    if counter % 10 == 0:
        print "ANOMALY! Publishing to MQTT topic..."
        event['anomaly'] = True
        client.publish(topic='dt/events', payload=json.dumps(event))

if __name__ == '__main__':
    test_event = {
        "power": 1102,
        "torque": 1171,
        "current": 1290,
        "frequency": 1142,
        "voltage": 1254,
        "time": "2018-10-17 04:55:02.662190",
        "speed_SPD": 300,
        "power_computed": 449.04683929931457
    }

    handler(test_event)
