FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y g++ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /sandbox