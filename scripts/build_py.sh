#!/bin/bash

OWD=$(pwd)

for dir in $(find ${PWD}/lambdas  -maxdepth 1 -mindepth 1 -type d );
do
  if [ -f $dir/requirements.txt ]; then
    echo "Installing Python dependencies for $dir ..."
    cd $dir
    rm -rf ./site-packages
    pip install -t ./site-packages/ -r ./requirements.txt
    cd $OWD
  fi
done