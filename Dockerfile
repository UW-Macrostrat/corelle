# Dockerfile for the corelle API server
FROM python:3.10

WORKDIR /code

ENV POETRY_VIRTUALENVS_CREATE=false

RUN apt-get -y update && apt-get -y install postgresql-client

RUN pip install poetry==1.2.2

COPY ./requirements.txt /code/

RUN pip install -r requirements.txt

COPY ./py-packages /code/py-packages

RUN poetry install

ENV CORELLE_DB=postgresql://postgres@database:5432/corelle

COPY ./bin/* /code/bin/

CMD poetry run /code/bin/run-docker
