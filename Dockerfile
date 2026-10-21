FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# One mount holds config.yaml and the folders scripts write into:
#   /config/config.yaml
#   /config/plex/
#   /config/kometa/
#   /config/tmdb/
ENV MEDIA_SCRIPTS_CONFIG_DIR=/config
VOLUME /config

ENTRYPOINT ["python", "/app/orchestrator.py"]
