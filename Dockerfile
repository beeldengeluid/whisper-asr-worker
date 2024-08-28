FROM docker.io/python:3.10@sha256:c6b64ba9c0f03c41e10f1e6053ca2ecf2dbced44098f8d56ed579aa50e839889 AS req

RUN python3 -m pip install pipx && \
  python3 -m pipx ensurepath

RUN pipx install poetry==1.7.1 && \
  pipx inject poetry poetry-plugin-export && \
  pipx run poetry config warnings.export false

COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml
RUN pipx run poetry export --format requirements.txt --output requirements.txt

FROM docker.io/python:3.10@sha256:c6b64ba9c0f03c41e10f1e6053ca2ecf2dbced44098f8d56ed579aa50e839889

# Create dirs for:
# - Injecting config.yml: /root/.DANE
# - Mount point for input & output files: /data
# - Storing the source code: /src
RUN mkdir \
  /data \
  /mnt/dane-fs \
  /model \
  /root/.DANE \
  /src

WORKDIR /src

COPY --from=req ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./ /src

# Write provenance info about software versions to file
RUN echo "dane-whisper-asr-worker;https://github.com/beeldengeluid/dane-whisper-asr-worker/commit/$(git rev-parse HEAD)" >> /software_provenance.txt

ENTRYPOINT ["./docker-entrypoint.sh"]
