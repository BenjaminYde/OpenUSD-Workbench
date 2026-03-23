#!/bin/bash

# create variables
BUILD_CONTEXT=$(dirname $0)
IMAGE_NAME=doxygen-1.16.1
PATH_DOCKERFILE=$BUILD_CONTEXT/Dockerfile

# docker build
echo -e "Building doxygen dockerfile...\n"

docker build \
    --rm \
    --file $PATH_DOCKERFILE \
    -t $IMAGE_NAME \
    $BUILD_CONTEXT

echo -e "Done building doxygen dockerfile!\n"