#!/bin/bash

SCRIPT_DIR=$(dirname $0)

# build dockerfile
$SCRIPT_DIR/build_docker_openusd_2508_py312.sh

# allow x11 in docker to forward gui to host
xhost +local:docker