# Dockerfile for the corelle API server
FROM python:3.10

WORKDIR /code

RUN pip install poetry==1.2.2

COPY ./api-server/poetry.lock ./api-server/pyproject.toml /code/

RUN poetry install --no-dev --no-root

COPY ./api-server/corelle_server ./corelle_server

RUN poetry install --no-dev

ENV CORELLE_DB=postgresql://postgres@database:5432/corelle

WORKDIR /run
COPY ./bin/* ./

CMD poetry run ./run-docker
