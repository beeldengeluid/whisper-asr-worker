#!/bin/sh

echo "Starting Whisper ASR worker"

python main.py "$@"

echo "The worker has finished"