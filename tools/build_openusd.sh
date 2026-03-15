#!/usr/bin/env bash

# go to openusd folder
CURRENT_DIR=$(dirname $0)
OPENUSD_FOLDER=$CURRENT_DIR/..
cd $OPENUSD_FOLDER/submodules/OpenUSD

# create log file location (created by cmake automatically when building)
LOG_DIR=./build/build/OpenUSD
LOG_FILE=$LOG_DIR/log.txt
mkdir -p $LOG_DIR
touch $LOG_FILE


# run openusd build (in the background by appending '&')
echo "Starting build and streaming log ($LOG_FILE)..."

python3 ./build_scripts/build_usd.py \
    -v \
    --vulkan --no-tutorials --no-examples \
    --build-monolithic \
    --cmake-build-args "-DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++" \
    ./build &

# get the process id python build exec
BUILD_PID=$!

# ensure background process is "trapped" when you press Ctrl+C, it kills the process
trap 'echo "Canceling build..."; kill -TERM $BUILD_PID 2>/dev/null; exit 1' SIGINT SIGTERM

# print the tail of the log file
# --pid=$BUILD_PID tells tail to automatically exit when the python script finishes
tail -f $LOG_FILE --pid=$BUILD_PID

# wait for the background process to finish and grab its exit code 
wait $BUILD_PID