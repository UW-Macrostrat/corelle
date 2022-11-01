# Dockerfile for the corelle API server
FROM python:3.10

WORKDIR /code

ENV POETRY_VIRTUALENVS_CREATE=false

RUN apt-get -y update && apt-get -y install postgresql-client

RUN pip install poetry==1.2.2

COPY ./poetry.lock ./pyproject.toml /code/
COPY ./py-packages/client/pyproject.toml /code/py-packages/client/
COPY ./py-packages/server/pyproject.toml /code/py-packages/server/
COPY ./py-packages/engine/pyproject.toml /code/py-packages/engine/

# We need to add shims for local development dependencies for poetry not to complain
COPY ./py-packages/client/corelle/client/__init__.py /code/py-packages/client/corelle/client/__init__.py
COPY ./py-packages/server/corelle/server/__init__.py /code/py-packages/server/corelle/server/__init__.py
COPY ./py-packages/engine/corelle/engine/__init__.py /code/py-packages/engine/corelle/engine/__init__.py

RUN poetry install --no-root

COPY ./py-packages /code/py-packages

RUN poetry install

ENV CORELLE_DB=postgresql://postgres@database:5432/corelle

COPY ./bin/* /code/bin/

CMD poetry run /code/bin/run-docker
