# dane-whisper-asr-worker

## Model options

If you prefer to use your own model that is stored locally, make sure to set `BASE_MOUNT_MODEL` to the path where the model files can be found. A model found locally will take precedence over downloading it from Huggingface or S3 (so, no matter how `WHISPER_ASR_SETTINGS.MODEL` is set, it will ignore it if a model is present locally).

The pre-trained Whisper model version can be adjusted in the `config.yml` file by editing the `MODEL` parameter within `WHISPER_ASR_SETTINGS`. Possible options are:

|Size|Parameters|
|---|---|
|`tiny`|39 M|
|`base`|74 M|
|`small`|244 M|
|`medium`|769 M|
|`large`|1550 M|
|`large-v2`|1550 M|
|`large-v3`|1550 M|

We recommend version `large-v2` as it performs better than `large-v3` in our benchmarks.

You can also specify an S3 URI if you have your own custom model available via S3.

## Running via Docker using a CUDA compatible GPU

To run it using a GPU via Docker, check [the instructions from the dane-example-worker](https://github.com/beeldengeluid/dane-example-worker/wiki/Containerization#running-the-container-locally-using-cuda-compatible-gpu).

Make sure to replace `dane-example-worker` in the `docker run` command with `dane-whisper-asr-worker`.