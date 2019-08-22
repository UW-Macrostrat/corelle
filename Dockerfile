# Dockerfile for the corelle API
FROM python:3.7-alpine

WORKDIR /install
COPY ./build-deps.sh .
RUN sh ./build-deps.sh

COPY ./requirements.txt .
RUN apk add --no-cache --virtual .build_deps git \
 && pip install -r requirements.txt \
 && apk del .build_deps
