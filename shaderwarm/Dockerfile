# shaderwarm — containerized (example; the tool is meant to run on the host
# where Steam lives, since it reads ~/.steam and launches the Steam client)
#
# Build:  docker build -t shaderwarm .
# Run:    docker run --rm -v $HOME/.steam:$HOME/.steam:ro \
#           -v $HOME/.local/share/Steam:$HOME/.local/share/Steam:ro shaderwarm scan
#
# Read-only mounts: shaderwarm only inspects on `scan`/`status`.

FROM python:3.11-slim

RUN useradd -m -u 1000 kraken
WORKDIR /opt/shaderwarm

COPY pyproject.toml ./
COPY src/ ./src/
COPY README.md ./
COPY LICENSE ./

RUN pip install --no-cache-dir . && rm -rf /root/.cache/pip

USER kraken
ENTRYPOINT ["shaderwarm"]
CMD ["--help"]
