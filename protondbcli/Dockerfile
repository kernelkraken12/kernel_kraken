# protondbcli — containerized (example; the tool runs fine without Docker)
#
# Build:  docker build -t protondbcli .
# Run:    docker run --rm protondbcli proton cairn
#         (or: docker run --rm -v $HOME/.cache:/home/kraken/.cache protondbcli proton cairn)

FROM python:3.11-slim

# The kraken-standard: no root in the container, XDG-friendly.
RUN useradd -m -u 1000 kraken
WORKDIR /opt/protondbcli

COPY pyproject.toml ./
COPY src/ ./src/
COPY README.md ./
COPY LICENSE ./

RUN pip install --no-cache-dir . && rm -rf /root/.cache/pip

USER kraken
ENV XDG_CACHE_HOME=/home/kraken/.cache

ENTRYPOINT ["proton"]
CMD ["--help"]
