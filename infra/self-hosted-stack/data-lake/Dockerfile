FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements-data-lake.txt /tmp/requirements-data-lake.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements-data-lake.txt

COPY scripts/data_lake /app/data_lake
COPY scripts/utils/_env.py /app/utils/_env.py
