# Greengrass ModBus Protocol Conversion

This is a codified version of AWS blog [Perform Protocol Conversion at the Edge with AWS Lambda and AWS Greengrass](https://aws.amazon.com/blogs/iot/perform-protocol-conversion-at-the-edge-with-aws-lambda-and-aws-greengrass/).

The Greengrass setup is defined as YAML in [`greengo.yaml`](./greengo.yaml) and deployed programmatically via AWS API. This way surely beats clicking through 19 screens on AWS console, and starting all over because you might fat-fingered something mid way.

In the blog, all Modbus components - device slave server, simulator client, and convertor client - are running as Lambdas on Greengrass for simplicity. I added a bit of realism by moving the device and the simulator out of Greengrass.


### Modbus
The `./modbus` contains the code I use to simulate Modbus device:

* `server.py` - Modbus Slave (Server): it simulates the machine PLC device.
* `simulator.py` - Simulator: it periodically writes a random number into a "Temp" holding register of Modbus Slave.
* `reader.py` - Reader: gets the value of the holding register. This code will move into the Greengrass Lambda function.

Run `server.py` and `simulator.py` in two terminals and watch the registers being updated. Check the current "Temp" with `reader.py`.