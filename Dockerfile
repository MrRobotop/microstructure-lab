FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        ninja-build \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md CMakeLists.txt Makefile ./
COPY cpp ./cpp
COPY src ./src
COPY api ./api
COPY dashboard ./dashboard
COPY tests ./tests
COPY docs ./docs

RUN python -m pip install --upgrade pip \
    && python -m pip install -e ".[all]"

CMD ["microstructure-lab", "--help"]
