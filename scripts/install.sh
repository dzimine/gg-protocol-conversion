# Greengrass settings and pre-reqs
sudo adduser --system ggc_user
sudo groupadd --system ggc_group

sudo apt-get update
sudo apt-get install -y sqlite3 python2.7 binutils curl

wget -O /vagrant/downloads/root.ca.pem http://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem

# Copy greengrass binaries
sudo tar -xzf /vagrant/downloads/greengrass-linux-x86-64-1.7.0.tar.gz -C /

# # Back up group.json - you'll thank me later
# sudo cp /greengrass/ggc/deployment/group/group.json /greengrass/ggc/deployment/group/group.json.orig

# Install Python and pip
sudo apt-get install -y python-dev python-setuptools gcc
sudo easy_install pip

# Install python dependencies for Lambda functions
# It includes the hack to put AWS Greengrass Core SDK from ./downloads in site-packages,
# because the damn thing doesn't install as a normal python dependency.
cd /vagrant
./scripts/build_py.sh

# Install Modbus requirements on the host, for Modbus slave and simulator
sudo pip install -r /vagrant/requirements.txt

# Post install steps:
# 1. run greengo on the host system to provision group in AWS
# 2. copy certificates - ./scripts/update_ggc.sh
# 3. sudo /greengrass/ggc/core/greengrassd start

