FROM python:3.8-slim

# === libopus install:
RUN apt-get update \
  && apt-get install -y \
    libopus0 \
    --no-install-recommends \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
ENV LIBOPUS /usr/lib/x86_64-linux-gnu/libopus.so.0

# === Python requirements:
RUN pip install --no-cache-dir pip-tools
COPY ./requirements.in /requirements.in
COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# === Actually run things:
COPY . /app
WORKDIR /app

CMD python run.py
