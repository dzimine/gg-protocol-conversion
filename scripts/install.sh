# Greengrass settings and pre-reqs
sudo adduser --system ggc_user
sudo groupadd --system ggc_group

sudo apt-get update
sudo apt-get install -y sqlite3 python2.7 binutils curl

wget -O /vagrant/downloads/root.ca.pem http://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem

# Copy greengrass binaries
sudo tar -xzf /vagrant/downloads/greengrass-ubuntu-x86-64-1.5.0.tar.gz -C /

# # Back up group.json - you'll thank me later
# sudo cp /greengrass/ggc/deployment/group/group.json /greengrass/ggc/deployment/group/group.json.orig

# Install Python and pip
sudo apt-get install -y python-dev python-setuptools gcc
sudo easy_install pip


# cd /greengrass/ggc/core
# sudo ./greengrassd start