#!/bin/bash

# prints message and exists 1 (i.e. no success)
die () {
    echo >&2 "$@"
    exit 1
}

# Starts the server on the port provided in the first argument (default port = 5303)
PORT="${1:-5333}"
echo $PORT | grep -E -q '^[0-9]+$' || die "Port number must be numeric, $PORT provided"

SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

# Load the environment vars
if [ -f "$SCRIPTPATH/../.env.override" ]; then
    set -a
    source $SCRIPTPATH/../.env.override
    set +a
else
    echo "No .env.override found"
fi

cd "$SCRIPTPATH/.."

flask --app app run --debug -p $PORT
