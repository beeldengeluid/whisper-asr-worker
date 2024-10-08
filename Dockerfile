FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y python3-pip python3.11-dev python-is-python3 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Create dirs for:
# - Storing the source code: /src
# - Storing the input & output files: /data
# - Storing the model: /model
RUN mkdir /src /data /model


WORKDIR /src

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install poetry==1.8.2

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# copy the rest into the source dir
COPY ./ /src

# Write provenance info about software versions to file
RUN echo "whisper-asr-worker;https://github.com/beeldengeluid/whisper-asr-worker/commit/$(git rev-parse HEAD)" >> /software_provenance.txt

ENTRYPOINT ["./docker-entrypoint.sh"]