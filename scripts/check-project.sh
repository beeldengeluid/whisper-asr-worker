#!/bin/sh

# copy this script to .git/hooks/pre-commit

SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
cd "$SCRIPTPATH"

poetry shell

cd ../

# run tests (configured in pyproject.toml)
echo "Running pytest"
pytest

# check lint rules (configured in .flake8)
echo "Running flake8"
flake8

# check formatting (configured in pyproject.toml)
echo "Running black"
black --check .

# check type annotations (configured in pyproject.toml)
echo "Running mypy"
mypy .
