#!/bin/bash

VERSION="1.9.0"
PLATFORM="x86-64"
GREENGRASS_RELEASE_URL=https://d1onfpft10uf5o.cloudfront.net/greengrass-core/downloads/${VERSION}/greengrass-linux-${PLATFORM}-${VERSION}.tar.gz

# Greengrass settings and pre-reqs
sudo adduser --system ggc_user
sudo groupadd --system ggc_group

sudo apt-get update
sudo apt-get install -y sqlite3 python2.7 binutils curl

# Install Python and pip
sudo apt-get install -y python-dev python-setuptools gcc
sudo easy_install pip

# Download and unpack greengrass binaries
wget $GREENGRASS_RELEASE_URL
GREENGRASS_RELEASE=$(basename $GREENGRASS_RELEASE_URL)
sudo tar -xzf $GREENGRASS_RELEASE -C /
rm $GREENGRASS_RELEASE

# Get root certificate
wget -O /vagrant/certs/root.ca.pem http://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem

# Back up group.json - you'll thank me later
sudo cp /greengrass/ggc/deployment/group/group.json /greengrass/ggc/deployment/group/group.json.orig

# Copy certificates and configurations
sudo cp /vagrant/certs/* /greengrass/certs
sudo cp /vagrant/config/* /greengrass/config

# # Install python dependencies for Lambda functions
# # It includes the hack to put AWS Greengrass Core SDK from ./downloads in site-packages,
# # because the damn thing doesn't install as a normal python dependency.
# cd /vagrant
# ./scripts/build_py.sh

# Install Modbus requirements on the host, for Modbus slave and simulator
sudo pip install -r /vagrant/requirements.txt

# Post install steps:
# 1. run greengo on the host system to provision group in AWS
# 2. copy certificates - ./scripts/update_ggc.sh
# 3. sudo /greengrass/ggc/core/greengrassd start

