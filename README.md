# whisper-asr-worker

ASR Worker that uses faster-whisper as the backend, to be used for transcribing AV material from B&G.

This is still a WIP, so it is subject to change.

There are 2 ways in which the whisper-asr-worker can be tested **(ON THE CPU)**:

## 1. Docker CPU run (recommended)

1. Check if Docker is installed
2. Make sure you have the `.env.override` file in your local repo folder
3. In `.env.override`, change `W_DEVICE` from `cuda` to `cpu`
4. Comment out the lines indicated in `docker-compose.yml`
5. Open your preferred terminal and navigate to the local repository folder
6. To build the image, execute the following command:
```
docker build . -t whisper-asr-worker
```
7. To run the worker, execute the following command:
```
docker compose up
```

## 2. Local CPU run

All commands should be run within WSL if on Windows or within your terminal if on Linux.

1. Follow the steps [here](https://github.com/beeldengeluid/dane-example-worker/wiki/Setting-up-a-new-worker) (under "Adding `pyproject.toml` and generating a `poetry.lock` based on it") to install Poetry and the dependencies required to run the worker
2. Make sure you have the `.env.override` file in your local repo folder
3. In `.env.override`, change `W_DEVICE` from `cuda` to `cpu`
4. Install `ffmpeg`. You can run this command, for example:
```
apt-get -y update && apt-get -y upgrade && apt-get install -y --no-install-recommends ffmpeg
```
5. Navigate to `scripts`, then execute the following command:
```
./run.sh
```

## Running the worker using a CUDA-compatible GPU

To run the worker with a CUDA-compatible GPU instead of the CPU, either:
- skip steps 3 & 4 from "Docker CPU run"
- skip step 3 from "Local run"

**(OUTDATED BUT STILL MIGHT BE RELEVANT)** To run it using a GPU via Docker, check [the instructions from the dane-example-worker](https://github.com/beeldengeluid/dane-example-worker/wiki/Containerization#running-the-container-locally-using-cuda-compatible-gpu).

Make sure to replace `dane-example-worker` in the `docker run` command with `dane-whisper-asr-worker`.

## Expected run

The expected run of this worker (whose pipeline is defined in `asr.py`) should

1. download the input file if it isn't downloaded already in `/data/input/` via `download.py`

2. download the model if not present via `model_download.py`

3. run `transcode.py` if the input file is a video to convert it to audio format (though there are plans to remove this and instead use the [audio-extraction-worker](https://github.com/beeldengeluid/audio-extraction-worker/) to extract the audio)

4. run `whisper.py` to transcribe the audio and save it in `/data/output/` if a transcription doesn't already exist
5. convert Whisper's output to DAAN index format using `daan_transcript.py`
6. (optional) transfer the output to an S3 bucket.

## Model options

If you prefer to use your own model that is stored locally, make sure to set `MODEL_BASE_DIR` to the path where the model files can be found. A model found locally will take precedence over downloading it from Huggingface or S3 (so, no matter how `W_MODEL` is set, it will ignore it if a model is present locally).

The pre-trained Whisper model version can be adjusted in the `.env` file by editing the `W_MODEL` parameter. Possible options are:

|Size|Parameters|
|---|---|
|`tiny`|39 M|
|`base`|74 M|
|`small`|244 M|
|`medium`|769 M|
|`large`|1550 M|
|`large-v2`|1550 M|
|`large-v3`|1550 M|

We recommend version `large-v2` as it performs better than `large-v3` in our [benchmarks](https://opensource-spraakherkenning-nl.github.io/ASR_NL_results/NISV/bn_nl/res_labelled.html).

You can also specify an S3 URI if you have your own custom model available via S3 (by modifying the `W_MODEL` parameter).
