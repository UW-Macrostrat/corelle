# Dockerfile for the corelle API server
FROM python:3.11
COPY --from=ghcr.io/astral-sh/uv:0.9.21 /uv /uvx /bin/
# https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers

WORKDIR /services/main

ENV UV_COMPILE_BYTECODE=1

RUN apt-get -y update && apt-get -y install postgresql-client gdal-bin libgdal-dev

# NEED TO specify another build context for the py-modules directory
COPY ./py-packages /services/main/py-packages
COPY pyproject.toml uv.lock /services/main/

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project


COPY ./bin/* /services/main/bin/


# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Needed for testing
ENV CORELLE_DB=postgresql://postgres@database:5432/corelle

EXPOSE 80

CMD ["uv", "run", "bin/run-docker"]
