import os
import sys
import json
import math
import copy

# Import installed packages (in site-packages)
site_pkgs = os.path.join(os.path.dirname(os.path.realpath(__file__)), "site-packages")
sys.path.append(site_pkgs)

import greengrasssdk  # noqa


# Creating a greengrass core sdk client
client = greengrasssdk.client('iot-data')

'''
Probabalistic Exponentially Weighted Moving Average PEWMA algorithm as described in
Carter, Kevin M., and William W. Streilein. "Probabilistic reasoning for streaming anomaly detection." Statistical Signal Processing Workshop (SSP), 2012 IEEE. IEEE, 2012.

The original code is from https://aws.amazon.com/blogs/iot/anomaly-detection-using-aws-iot-and-aws-lambda/
As Greengrass lambda can be long-running, the time-series points are stored in memory
between invocations (no need for DynamoDB). I also removed decimal/float magic.
'''

'''
The parameters than need to be changed for a different data set are T, ALPHA_0, BETA, DATA_COLS and KEY_PARAM
-T: number of points to consider in initial average
-ALPHA_0: base amount of PEWMA which is made up from previous value of PEWMA
-BETA: parameter that controls how much you allow outliers to affect your MA, for standard EWMA set to 0
-THRESHOLD: value below which a point is considered an anomaly, like a probability but not strictly a probability
-DATA_COLS: columns we want to take PEWMA of
-KEY_PARAM: key from event which will become dynamo key
'''

print "Starting up..."

# TODO: use Env variables
T = 30
ALPHA_0 = 0.95
BETA = 0.5
THRESHOLD = .05
DATA_COLS = ["torque"]
KEY_PARAM = "device_id"
TOPIC = 'dt/device_anomalies'


class Table(object):
    '''
    In-memory storage with DynamoDB like interface to preserve resablance with the cloud version
    of this lambda from https://aws.amazon.com/blogs/iot/anomaly-detection-using-aws-iot-and-aws-lambda/
    '''

    def __init__(self, keyname):
        self._db = {}
        self._keyname = keyname

    def get_item(self, Key):
        key = Key[self._keyname]
        print key
        return self._db.get(key)

    def put_item(self, Item):
        key = Item[self._keyname]
        self._db[key] = Item

# Run Lambda as "lnog-running" (aka "pinned") to keep values in variables,
# yet it will respond to Subscription events.

counter = 0  # Anomaly counter, just for fun
table = Table(KEY_PARAM)  # Stores T previous records between runs


def handler(event, context):

    print "------ Event"
    print event
    response = table.get_item(Key={KEY_PARAM: event[KEY_PARAM]})  # get record from dynamodb for this sensor
    if response:
        newRecord = response
        newRecord = update_list_of_last_n_points(event, newRecord, DATA_COLS, T)
        newRecord = generate_pewma(newRecord, event, DATA_COLS, T, ALPHA_0, BETA, THRESHOLD)
    else:
        newRecord = initial_record(event, DATA_COLS)
        print "Writing initial record:"
        print newRecord

    publish(newRecord, DATA_COLS)
    table.put_item(Item=newRecord)  # write new record to the table

    return newRecord


def update_list_of_last_n_points(event, current_data, data_cols, length_limit):
    '''
    this function updates lists that contain length_limit # of most recent points
    '''
    new_data = current_data
    for col in event:
        if col in data_cols:
            append_list = current_data[col]
            append_list.append(event[col])
            if len(append_list) > length_limit:
                append_list = append_list[1:]
            new_data[col] = append_list
        else:
            new_data[col] = event[col]
    return new_data


def initial_record(event, data_cols):
    '''
    if there is no record in the table for this sensorid then this will generate
    the record which will be the initial record
    '''
    newRecord = copy.deepcopy(event)
    for col in event:
        if col in data_cols:
            newRecord[col] = [newRecord[col]]
            newRecord["alpha_" + col] = 0
            newRecord["s1_" + col] = event[col]
            newRecord["s2_" + col] = math.pow(event[col], 2)
            newRecord["s1_next_" + col] = newRecord["s1_" + col]
            newRecord["STD_next_" + col] = \
                math.sqrt(newRecord["s2_" + col] - math.pow(newRecord["s1_" + col], 2))
        else:
            newRecord[col] = newRecord[col]
    return newRecord


def generate_pewma(newRecord, event, data_cols, T, alpha_0, beta, threshold):
    for col in data_cols:
        t = len(newRecord[col])
        newRecord["s1_" + col] = newRecord["s1_next_" + col]
        newRecord["STD_" + col] = newRecord["STD_next_" + col]
        try:
            newRecord["Z_" + col] = (event[col] - newRecord["s1_" + col]) / newRecord["STD_" + col]
        except ZeroDivisionError:
            newRecord["Z_" + col] = 0

        newRecord["P_" + col] = \
            1 / math.sqrt(2 * math.pi) * math.exp(-math.pow(newRecord["Z_" + col], 2) / 2)
        newRecord["alpha_" + col] = \
            calc_alpha(newRecord, t, T, col, beta, alpha_0)
        newRecord["s1_" + col] = \
            newRecord["alpha_" + col] * newRecord["s1_" + col] + (1 - newRecord["alpha_" + col]) * event[col]
        newRecord["s2_" + col] = \
            newRecord["alpha_" + col] * newRecord["s2_" + col] + (1 - newRecord["alpha_" + col]) * math.pow(event[col], 2)
        newRecord["s1_next_" + col] = newRecord["s1_" + col]
        newRecord["STD_next_" + col] = \
            math.sqrt(newRecord["s2_" + col] - math.pow(newRecord["s1_" + col], 2))
        isAnomaly = newRecord["P_" + col] <= threshold
        newRecord[col + "_is_Anomaly"] = isAnomaly

        newRecord['anomaly'] = isAnomaly
        if isAnomaly:
            newRecord['metric'] = col
            newRecord['value'] = event[col]
        else:
            newRecord.pop('value', None)

    return newRecord


def calc_alpha(newRecord, t, T, col, beta, alpha_0):
    if t < T:
        alpha = 1 - 1.0 / t
        print "EWMA calc in progress (initialization of MA) -" + col
    else:
        alpha = (1 - beta * newRecord["P_" + col]) * alpha_0
        print "EWMA calc in progress-" + col
    return alpha


def publish(newRecord, data_cols):
    global counter
    if newRecord.get('anomaly'):
        counter += 1
        print "-----ANOMALY FOUND![{0}]".format(counter)

        # Take record, drop the running table, keep the last value
        event = copy.deepcopy(newRecord)
        for col in data_cols:
            event[col] = event[col][-1]

        payload = json.dumps(event, indent=4)
        print payload
        client.publish(topic=TOPIC, payload=json.dumps(event))

if __name__ == '__main__':
    ''' Use for local testing. '''

    test_event = {
        "power": 1,
        "torque": 75,
        "torquePercent": 273,
        "torqueNm": 1,
        "current": 7,
        "frequency": 98,
        "voltage": 40,
        "speed_SPD": 301,
        "device_id": "dev_0",
        "power_computed": 4.298362528560548
    }

    filename = sys.argv[1] if 1 < len(sys.argv) else 'reads.json'

    # Read JSON-chunk file
    with open(filename) as f:
        for i, line in enumerate(f.readlines()):
            print "RECORD " + str(i)
            event = json.loads(line)
            r = handler(event, None)

    print "{0} anomalies found.".format(counter)
