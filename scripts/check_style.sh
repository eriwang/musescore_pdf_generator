#! /usr/bin/env bash

npx eslint .
ESLINT_RC=$?

pylint src/
PYLINT_RC=$?

if [[ ($ESLINT_RC != 0) || ($PYLINT_RC != 0) ]]; then
    echo "Found linting errors, see output for details" 1>&2
    exit 1
fi
