#!/usr/bin/env bash

# go into the python directory
CURRENT_DIR=$(dirname $0)
cd $CURRENT_DIR/../..

# generate the stubs
rm -rf ./stubs || true
python3 ./tools/stubs/generate_usd_stubs.py --output-dir ./stubs