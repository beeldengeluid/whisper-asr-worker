#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
LOW_RES_THROTTLER="http://your-host/viz"
DEV_WORKSPACE_ROOT="/home/YOU/workspace"
DOCKER_IMAGE="917951871879.dkr.ecr.eu-west-1.amazonaws.com/kaldi_nl:v1.2"
INPUT_FILE=$1
INPUT_DIR=$DEV_WORKSPACE_ROOT/dane-asr-worker/data

if [ -z "$1" ]
  then
    echo "Please supply an input file"
    exit 1
fi

while read LINE; do
    PID=`echo $LINE | cut -d';' -f1`
    CARRIER_ID=`echo $LINE | cut -d';' -f2`
    echo "Program ID: $PID"
    echo "Carrier ID: $CARRIER_ID"
    FILE_ID="${PID}__${CARRIER_ID}"
    echo "File ID: $FILE_ID"

    MP4="$INPUT_DIR/$FILE_ID.mp4"
    MP3="$INPUT_DIR/$FILE_ID.mp3"
    OUTPUT_DIR="$INPUT_DIR/output/$FILE_ID"
    # only download if it's not there yet
    if ! [ -f $MP4 ] ; then
        echo "Downloading $CARRIER_ID";
        curl "${LOW_RES_THROTTLER}/${CARRIER_ID}" -o $MP4;
    fi
    # only transcode if it's not there yet
    if ! [ -f $MP3 ] ; then
        echo "Extracting audio from $MP4";
        # ffmpeg -nostdin -y -i $MP4 -ar 16000 -ac 1 -b:a 256k $MP3 -v quiet;
        ffmpeg -y -i $MP4 $MP3;
        echo "done with this one";
    fi
    # only extract OUTPUT_DIR if it's not there yet
    if ! [ -d $OUTPUT_DIR ] ; then
        mkdir -p $OUTPUT_DIR
        echo "Generating transcript from $MP3";
        docker run --rm -v $DEV_WORKSPACE_ROOT/dane-asr-worker/models:/models -v $INPUT_DIR:/data $DOCKER_IMAGE ./decode_OH.sh /data/$FILE_ID.mp3 /data/output/$FILE_ID
    fi
done <$INPUT_FILE
