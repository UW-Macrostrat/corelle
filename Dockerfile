# Dockerfile for the corelle API
FROM python:3.10

WORKDIR /code

RUN pip install poetry==1.2.2

COPY ./corelle-api-server/poetry.lock ./corelle-api-server/pyproject.toml /code/

RUN poetry install --no-dev --no-root

COPY ./corelle-api-server/corelle_server ./corelle_server

RUN poetry install --no-dev --no-root

ENV CORELLE_DB=postgresql://postgres@database:5432/corelle

WORKDIR /run
COPY ./bin/* ./

CMD ./run-docker
