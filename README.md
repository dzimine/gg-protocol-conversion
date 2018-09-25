# Greengrass ModBus Protocol Conversion

This is a codified version of AWS blog [Perform Protocol Conversion at the Edge with AWS Lambda and AWS Greengrass](https://aws.amazon.com/blogs/iot/perform-protocol-conversion-at-the-edge-with-aws-lambda-and-aws-greengrass/).

The Greengrass setup is defined as YAML in [`greengo.yaml`](./greengo.yaml) and deployed programmatically via AWS API. This way surely beats clicking through 19 screens on AWS console, and starting all over because you might fat-fingered something mid way.

In the blog, all Modbus components - device slave server, simulator client, and convertor client - are running as Lambdas on Greengrass for simplicity. I added a bit of realism by moving the device and the simulator out of Greengrass.


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
* AWS CLI [installed](http://docs.aws.amazon.com/cli/latest/userguide/installing.html) and credentials [configured](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html). Consider using [named profiles](https://docs.aws.amazon.com/cli/latest/userguide/cli-multiple-profiles.html).

### Setup

0. Create Vagrant VM. It will create Ubuntu 16 VM and install Greengrass Core on it. Check [`Vagrantfile`](./Vagrantfile) and [`./scripts/install.sh`](./scripts/install.sh) to understandwhat is happening.

1. Install [`greengo`](http://greengo.io). It's a tool to describe Greengrass deployment as YAML and push it to AWS.  Saves tons of clicks on AWS Console. Use the head of `master` branch.

    ```
    pip install git+git://github.com/dzimine/greengo.git#egg=greengo
    ```

2. Configure AWS API keys. All we need are `~/.aws/config` and `~/.aws/credentials` files; do this manually ([follow instructions here](https://docs.aws.amazon.com/cli/latest/userguide/cli-config-files.html)), or install [AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/installing.html) which will guide you.

3. Create a Greengrass Core definition in AWS. See [./greengo.yaml](./greengo.yaml) for what will be created.

    ```
    greengo create
    ```
    
    Use AWS Console to explore & appreciate what had been created. 
    
3. Now that the definitions are created, the certificates for the Greengrass Core are copied under `./certs`, and greengrassd configuration generated under `./config`. To move them where they belong, run `./scripts/update_ggc.sh`  on the Vagrant VM.

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