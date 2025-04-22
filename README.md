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

## Using the API
### Accessing the endpoint

To access the worker and schedule runs, go to the following link: http://localhost:5333/docs.

In there, you have the following options:
1. `GET /tasks`: returns a list of all tasks that have run or are currently running/scheduled to run
2. `POST /tasks`: schedule a new task to transcribe the input URI and export it to the output URI. The format of a task is the following:
```
{
  "input_uri": "string",
  "output_uri": "string",
  "status": "CREATED | PROCESSING | DONE | ERROR",
  "id": "string",
  "error_msg": "string",
  "response": {}
}
```

The only thing you need to absolutely have is the `input_uri`. The `output_uri` can stay empty in which case the generated transcripts will be stored locally, and the rest of the fields will be automatically generated or updated throughout the task's process.

3. `GET /status`: returns the status of the worker:
- `503` if the worker is currently executing a task
- `200` if the worker is available to run new tasks

4. `GET /tasks/{task_id}`: returns the task details of the given `task_id`

5. `DELETE /tasks/{task_id}`: deletes the task with the given `task_id`

6. `GET /ping`: returns `pong` (can be ignored, not relevant to the main functionality of the worker)

## Expected run when scheduling a new task

The expected run of this worker (whose pipeline is defined in `asr.py`) should

1. download the input file if it isn't downloaded already in `/data/input/` via `download.py`

2. download the model if not present via `model_download.py`

3. run `transcode.py` if the input file is a video to convert it to audio format (though there are plans to remove this and instead use the [audio-extraction-worker](https://github.com/beeldengeluid/audio-extraction-worker/) to extract the audio)

4. run `whisper.py` to transcribe the audio and save it in `/data/output/` if a transcription doesn't already exist
5. convert Whisper's output to DAAN index format using `daan_transcript.py`
6. (optional) transfer the output to an S3 bucket.

## Model options

If you prefer to use your own model that is stored locally, make sure to set `MODEL_BASE_DIR` to the path where the model files can be found.

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

You can also specify an S3/HTTP URI if you want to load your own (custom) model (by modifying the `W_MODEL` parameter).

## Config

The parameters used to configure the application can be found under `.env` file. You will also need to create a `.env.override` file that contains secrets related to the S3 connection that should normally not be exposed in the `.env` file. The parameters that should be updated with valid values in the `.env.override` are:

- `S3_ENDPOINT_URL`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
