FROM python:3.12-slim

WORKDIR /app
COPY gamesage/ gamesage/
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .

# Example: run the auto-watch mode inside a container (needs host sensors
# mounted read-only to be useful: -v /sys/class/hwmon:/sys/class/hwmon:ro)
ENTRYPOINT ["gamesage"]
CMD ["--help"]
