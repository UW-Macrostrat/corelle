# Dockerfile for the corelle API server
FROM python:3.10

WORKDIR /code

RUN pip install poetry==1.2.2

COPY ./poetry.lock ./pyproject.toml /code/
COPY ./py-packages/client/pyproject.toml /code/py-packages/client/
COPY ./py-packages/server/pyproject.toml /code/py-packages/server/
COPY ./py-packages/engine/pyproject.toml /code/py-packages/engine/

ENV POETRY_VIRTUALENVS_CREATE=false

COPY ./py-packages /code/py-packages

RUN poetry install

ENV CORELLE_DB=postgresql://postgres@database:5432/corelle

COPY ./bin/* /code/bin/

CMD poetry run /code/bin/run-docker
