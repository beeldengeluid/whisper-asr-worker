FROM docker.io/python:3.11 AS req

RUN python3 -m pip install pipx && \
  python3 -m pipx ensurepath

RUN pipx install poetry==1.8.2 && \
  pipx inject poetry poetry-plugin-export && \
  pipx run poetry config warnings.export false

COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml
RUN pipx run poetry export --format requirements.txt --output requirements.txt

FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

# Install Python & ffmpeg
RUN apt-get update && \
    apt-get install -y python3.11-dev python3-pip python-is-python3 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Ensure Python 3.11 is used (for some reason, 3.10 is also installed...)
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Create dirs for:
# - Storing the source code: /src
# - Storing the input & output files: /data
# - Storing the model: /model
RUN mkdir /src /data /model

WORKDIR /src

COPY --from=req ./requirements.txt requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

# copy the rest into the source dir
COPY ./ /src

# # Get git commit info, then delete the .git folder
# RUN git rev-parse HEAD >> git_commit
# RUN rm -rf .git

ENTRYPOINT ["./docker-entrypoint.sh"]