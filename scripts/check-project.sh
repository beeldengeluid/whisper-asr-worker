#!/bin/sh

# copy this script to .git/hooks/pre-commit

SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
cd "$SCRIPTPATH"

poetry env activate

cd ../

# run tests (configured in pyproject.toml)
echo "Running pytest"
poetry run pytest

# check lint rules (configured in .flake8)
echo "Running flake8"
poetry run flake8

# check formatting (configured in pyproject.toml)
echo "Running black"
poetry run black --check .

# check type annotations (configured in pyproject.toml)
echo "Running mypy"
poetry run mypy .
