#!/bin/sh

echo "Starting DANE Whisper ASR worker"

python worker.py "$@"

echo "The worker has finished"
