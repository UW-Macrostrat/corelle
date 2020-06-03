# Dockerfile for the corelle API
FROM python:3.7-alpine

WORKDIR /install
COPY ./build-deps.sh .
RUN sh ./build-deps.sh

COPY ./requirements.txt .

# psycopg2-binary doesn't work under alpine linux but is needed
# for local installation
RUN sed -i 's/psycopg2-binary/psycopg2/g' requirements.txt \
 && pip install -r requirements.txt

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
