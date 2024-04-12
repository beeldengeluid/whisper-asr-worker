#!/bin/sh

echo "Starting DANE Whisper ASR worker"

poetry run python worker.py "$@"

echo "The worker has finished"