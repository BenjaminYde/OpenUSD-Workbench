#!/bin/bash

# setup stderr
set -e

# variables
SCRIPT_DIR=$(dirname $0)
cd $SCRIPT_DIR

# clean files
rm -rf build || true

# configure
cmake --preset linux-clang-debug

# build
cmake --build --preset linux-clang-debug

# execute
echo -e "🚀 Executing..."
./build/linux-clang-debug/MyTarget 