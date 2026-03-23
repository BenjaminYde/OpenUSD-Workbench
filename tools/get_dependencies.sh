#!/bin/bash

# go to git root folder
SCRIPT_DIR=$(dirname $0)
GIT_ROOT_DIR=$SCRIPT_DIR/..
cd $GIT_ROOT_DIR

# clone git submodules
git submodule init
git submodule update --recursive \
    submodules/OpenUSD