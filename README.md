# Greengrass ModBus Protocol Conversion

This is a codified version of the demo presented at [AWS re:Invent 2018, session IOT365](https://www.portal.reinvent.awsevents.com/connect/sessionDetail.ww?SESSION_ID=92026). It uses AWS Greengrass to pull IIoT data off Modbus devices, run Modbus to MQTT protocol conversion, send data to the AWS IoT. It also runs a local anomaly detection, and closes the control loop with new *AWS Greengrass Modubs connector*. 


> WARNING: AWS Modubs Connector has beenmodified to support TCP; the modification is not included for licensing reasons; you are smart enough to do it on your own. Or, stay tuned for AWS publishing the TCP version of Modbus connector.

The concept is partially inspired by AWS blog [Perform Protocol Conversion at the Edge with AWS Lambda and AWS Greengrass](https://aws.amazon.com/blogs/iot/perform-protocol-conversion-at-the-edge-with-aws-lambda-and-aws-greengrass/). In contrast, however, the Greengrass setup is defined as YAML in [`greengo.yaml`](./greengo.yaml) and deployed programmatically via AWS API. This way surely beats clicking through 19 screens on AWS console, and
starting all over because you might fat-fingered something mid way.



## Modbus
The `./modbus` contains the code I use to simulate Modbus device:

* `server.py` - Modbus Slave (Server): it simulates the machine PLC device.
* `simulator.py` - Simulator: it periodically writes a random number into a "Temp" holding register of Modbus Slave.
* `reader.py` - Reader: gets the value of the holding register. This code will move into the Greengrass Lambda function.

Run `server.py` and `simulator.py` in two terminals and watch the registers being updated. Check the current "Temp" with `reader.py`


## Greengrass Dev Env setup

### Pre-requisits

* A computer with Linux/MacOS, Python, git (dah!)
* [Vagrant](https://www.vagrantup.com/docs/installation/) with [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
* AWS CLI [installed](http://docs.aws.amazon.com/cli/latest/userguide/installing.html) and credentials
  [configured](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html).
  Consider using [named profiles](https://docs.aws.amazon.com/cli/latest/userguide/cli-multiple-profiles.html).

### Setup

0. Create Vagrant VM. It will create Ubuntu 16 VM and install Greengrass Core on it. Check [`Vagrantfile`](./Vagrantfile) and [`./scripts/install.sh`](./scripts/install.sh) to understandwhat is happening.

1. Install [`greengo`](http://greengo.io). It's a tool to describe Greengrass deployment as YAML and
   push it to AWS.  Saves tons of clicks on AWS Console. Use the head of `master` branch, to pick the latest changes.

    ```
    pip install git+git://github.com/dzimine/greengo.git#egg=greengo
    ```

    Build python dependencies for Lambda functions. Each lambda under `./lambdas` is supposed to
    contain `requirements.txt`. To simplifiy, run `build-py.sh` that will pull lambda requirements.

    ```
    ./scripts/build-py.sh
    ```

2. Configure AWS API keys. All we need are `~/.aws/config` and `~/.aws/credentials` files; do this
manually ([follow instructions here](https://docs.aws.amazon.com/cli/latest/userguide/cli-config-
files.html)), or install [AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/installing.html)
which will guide you.

3. Create a Greengrass Core definition in AWS. See [./greengo.yaml](./greengo.yaml) for what will be created.

    ```
    greengo create
    ```

    Use AWS Console to explore & appreciate what had been created.

3. Now that the definitions are created, the certificates for the Greengrass Core are copied under
`./certs`, and greengrassd configuration generated under `./config`. To move them where they belong,
run `./scripts/update_ggc.sh`  on the Vagrant VM.

    ```
    ./scripts/update_ggc.sh
    ```

4. Start Greengrass Core

    ```
    sudo /greengrass/ggc/core/greengrassd start
    ```

    Deploy definition. Deployment pushes the code and definitions from the cloud and run it on the local GGC.

    ```
    greengo deploy
    ```

    Observe the deployment by watching the `runtime.log` file:

    ```
    sudo tail -f /greengrass/ggc/var/log/system/runtime.log
    ```

    When deployment completes, the Lambda will be running. Watch the logs (don't forget to use YOUR `$REGION` and `$ACCOUNT` below):

    ```
    tail -f /greengrass/ggc/var/log/user/$REGION/$ACCOUNT/ModbusToAWSIoT.log
    ```


# GreenGate:

To test a value:
```
{
    "slave": {
        "host": "192.168.0.13",
        "port": 502
    },
    "request": {
        "request_id": "TestRequest",
        "operation": "ReadHoldingRegistersRequest",
        "device": 248,
        "address": 8529,
        "count": 1
    }
}
```

To simulate anomaly:
```
{
    "slave":{
    "host":"localhost",
    "port":5020
    },
    "request":{
        "request_id": "SimulateTorqueAnomaly",
        "operation": "WriteSingleRegisterRequest",
        "device": 1,
        "address": 3205,
        "value": 140
    }
}
```

To start the motor: 
```
{
    "slave":{
        "host": "192.168.0.13",
        "port": 502
    },
    "request":{
        "request_id": "StartTheMotor",
        "operation": "WriteSingleRegisterRequest",
        "device": 248,
        "address": 8502,
        "value": 140
    }
}
```


## Other

The data are being sent to AWS IoT via MQTT, now what? You likely want to save them, do something
with them, and report back. The two options are AWS IoT Analytics, and Elastic Search. The way to go
is to set up IoT Rule that sends the MQTT topic to the correspondent service. It's always a good
idea to set up an Error action to "Republish message to an AWS IoT topic" (say `rules/errors`) so
you can see when things go wrong.

The rest of the setup can also be codified but is currently set up manually via AWS console. Below
I drop some notes on how to do it.

The [es_mapping.json](./es_mapping.json) file contains a proper ES index type setup, use PUT
on ES endpoint to create index prior (!!!) to sending traffic there.
