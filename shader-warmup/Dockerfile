FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY shader_warmup ./shader_warmup

RUN pip install --no-cache-dir .

ENTRYPOINT ["shader-warmup"]
