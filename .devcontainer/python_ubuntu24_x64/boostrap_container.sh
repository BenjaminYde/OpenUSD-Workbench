#!/usr/bin/env bash

CURRENT_DIR=$(dirname $0)
cd $CURRENT_DIR

# configure shell rc's:
for shellrc in .shrc .bashrc .zshrc; do
    cat shellrc >> ~/$shellrc
done