# Dockerfile for the corelle API
<<<<<<< HEAD
FROM python:3.10

WORKDIR /code

RUN pip install poetry==1.2.2

COPY ./corelle-api-server/poetry.lock ./corelle-api-server/pyproject.toml /code/
=======
FROM python:3.8-alpine

# Script to build the dependencies needed
# for the Corelle backend
# Note: `apk` is the package-management equivalent of `apt`
# for Alpine Linux.
RUN apk update && apk upgrade
RUN apk add --no-cache python3-dev libstdc++ openblas \
  libpq postgresql-dev postgresql-client \
  bash curl

##
###
# Deps for fiona importer
RUN apk add --no-cache \
  --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing \
  --repository http://dl-cdn.alpinelinux.org/alpine/edge/main \
  geos \
  gdal-dev \
  proj

# Install Poetry & ensure it is in $PATH
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | POETRY_PREVIEW=1 python
ENV PATH "/root/.poetry/bin:/opt/venv/bin:${PATH}"
ENV POETRY_VIRTUALENVS_CREATE false

RUN apk add --no-cache --virtual .build_deps gcc g++ gfortran \
  musl-dev python3-dev
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h

RUN pip install --no-cache-dir numpy==1.20.2
RUN pip install --no-cache-dir numba==0.53.1
RUN pip install --no-cache-dir scipy==1.6.2
RUN pip install --no-cache-dir psycopg2==2.8.6
RUN pip install --no-cache-dir numpy-quaternion==2021.4.5
RUN pip install --no-cache-dir fiona==1.18.19

RUN rm /usr/include/xlocale.h && apk del .build_deps

COPY ./pyproject.toml .

# psycopg2-binary doesn't work under alpine linux but is needed
# for local installation
RUN sed -i 's/psycopg2-binary/psycopg2/g' pyproject.toml \
  && && poetry export --without-hashes -f requirements.txt --dev \
  |  poetry run pip install -r /dev/stdin

>>>>>>> poetry

RUN poetry install --no-dev --no-root

COPY ./corelle-api-server/corelle_server ./corelle_server

RUN poetry install --no-dev --no-root

ENV CORELLE_DB=postgresql://postgres@database:5432/corelle

<<<<<<< HEAD
=======
# For importing data

>>>>>>> poetry
WORKDIR /run
COPY ./bin/* ./

CMD poetry run ./run-docker
