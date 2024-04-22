# dane-whisper-asr-worker

## Model versions

The Whisper model version can be adjusted in the `config.yml` file by editing the `MODEL_VERSION` parameter within `WHISPER_ASR_SETTINGS`. Possible options are:

|Size|Parameters|
|---|---|
|`tiny`|39 M|
|`base`|74 M|
|`small`|244 M|
|`medium`|769 M|
|`large`|1550 M|
|`large-v2`|1550 M|
|`large-v3`|1550 M|

We recommend version `large-v2` as it performs better in most cases than `large-v3`.

## Running via Docker using a CUDA compatible GPU

Make sure that Docker runs within WSL. To do so, follow the last 3 bullets from [Adding `Dockerfile` and testing if it runs](https://github.com/beeldengeluid/dane-example-worker/wiki/Setting-up-a-new-worker#adding-dockerfile-and-testing-if-it-runs).

Additionally, you need to configure the NVIDIA Container Toolkit. To do so, follow the [installation steps](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#installation) and [configure the Docker runtime](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#configuring-docker).

Lastly, set `DEVICE` in `WHISPER_ASR_SETTINGS` of `config.yml` to `cuda`, then run the following command (from within the repository folder):

```
docker run \
    --gpus=all \
    --mount type=bind,source="$(pwd)"/config,target=/root/.DANE \
    --mount type=bind,source="$(pwd)"/data,target=/data \
    --rm \
    dane-example-worker --run-test-file
```