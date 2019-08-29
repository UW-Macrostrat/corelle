# Dockerfile for the corelle API
FROM python:3.7-alpine

WORKDIR /install
COPY ./build-deps.sh .
RUN sh ./build-deps.sh

COPY ./requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /module
COPY ./setup.py /module/
COPY ./corelle /module/corelle/

RUN pip install -e .
ENV CORELLE_DB=postgresql://postgres@database:5432/corelle

# For importing data
RUN apk add --no-cache curl bash

WORKDIR /run
COPY ./bin/load-features ./
COPY ./run-docker .

CMD ./run-docker
