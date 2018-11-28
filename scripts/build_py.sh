#!/bin/bash

OWD=$(pwd)

for dir in $(find ${PWD}/lambdas  -maxdepth 1 -mindepth 1 -type d );
do
  if [ -f $dir/requirements.txt ]; then
    echo "Installing Python dependencies for $dir ..."
    cd $dir
    rm -rf ./site-packages
    pip install -t ./site-packages/ -r ./requirements.txt

    if grep -q greengrass_core_sdk requirements.txt ; then
      echo "Adding greengrass core SDK for $dir ..."
      tar -xzf ../../downloads/greengrass-core-skd-1.2.0-dz.tar.gz -C ./site-packages
    fi

    cd $OWD
  fi

done