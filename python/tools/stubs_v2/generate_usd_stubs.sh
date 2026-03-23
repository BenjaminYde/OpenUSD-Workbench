#!/usr/bin/env bash

# go into the python directory
CURRENT_DIR=$(dirname $0)
REPO_DIR=$(realpath $CURRENT_DIR/../../..)
cd $REPO_DIR

# generate the stubs
rm -rf ./stubs || true
./python/tools/stubs_v2/usdstubgen.py --builddir ./python/stubs ./submodules/OpenUSD/build/docs/doxy_xml ./submodules/OpenUSD ./submodules/OpenUSD/build/lib/python