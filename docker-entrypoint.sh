#!/bin/sh

echo "Starting Whisper ASR worker"

poetry run python main.py "$@"

echo "The worker has finished"