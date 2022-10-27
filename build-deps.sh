#!/bin/sh
# Script to build the dependencies needed
# for the Corelle backend
# Note: `apk` is the package-management equivalent of `apt`
# for Alpine Linux.
apk update
apk upgrade
apk add --no-cache python3-dev libstdc++ openblas \
    libpq postgresql-dev postgresql-client \
    bash curl

##
###
# Deps for fiona importer
apk add --no-cache \
    --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing \
    --repository http://dl-cdn.alpinelinux.org/alpine/edge/main \
    geos \
    gdal-dev \
    proj

apk add --no-cache --virtual .build_deps gcc g++ gfortran \
    musl-dev python3-dev
ln -s /usr/include/locale.h /usr/include/xlocale.h

pip install --no-cache-dir numpy==1.20.2
pip install --no-cache-dir numba==0.53.1
pip install --no-cache-dir psycopg2==2.8.6
pip install --no-cache-dir numpy-quaternion
pip install --no-cache-dir fiona
pip install --no-cache-dir greenlet

apk del .build_deps
rm /usr/include/xlocale.h
