#! /usr/bin/env bash

# Requirements
REQ_PYTHON_MAJOR_VERSION=3
REQ_MIN_PYTHON_VERSION=3.6

# Functions

function get_python_version {
    echo $($1 -V 2>&1 | egrep -o "[0-9\.]*")
}

if [[ ($1 == "-h") || ($1 == "--help") ]]; then
    echo "USAGE: scripts/setup.sh <optional_python3_binary_location>. Should be run from repo root"
    exit 0
fi

# Sanity check folders
if [[ -d venv/ || -d node_modules ]]; then
    echo "Found at least one of venv/ node_modules, did you mean to run update.sh instead?"
fi

# Validate Python version

PYTHON_BIN=${1:-python3}
PYTHON_VERSION=$(get_python_version $PYTHON_BIN)
PYTHON_MAJOR_VERSION=$(echo $PYTHON_VERSION | egrep -o "^[0-9]*")

if [[ $PYTHON_MAJOR_VERSION != $REQ_PYTHON_MAJOR_VERSION ]]; then
    echo "Expected to be run with Python major version $REQ_PYTHON_MAJOR_VERSION," \
         "got $PYTHON_MAJOR_VERSION instead" 1>&2 
    exit 1
fi

if [[ $PYTHON_VERSION < $REQ_MIN_PYTHON_VERSION ]]; then
    echo "Expected to be run with at least Python $REQ_MIN_PYTHON_VERSION," \
         "got $PYTHON_VERSION instead" 1>&2
    exit 1   
fi

# Install hooks

ln -s $(pwd)/scripts/hooks/pre-commit.sh .git/hooks/pre-commit  # WSL seems to need full path for Windows for some reason?

# Not sure if any other versions need to be checked. Not checking for now.

virtualenv --python=$PYTHON_BIN venv

scripts/update.sh

echo "Setup complete."