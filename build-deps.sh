#!/bin/sh
# Script to build the dependencies needed
# for the Corelle backend
# Note: `apk` is the package-management equivalent of `apt`
# for Alpine Linux.
apk update
apk upgrade
apk add --no-cache python3-dev libstdc++ openblas \
    libpq postgresql-dev postgresql-client
apk add --no-cache --virtual .build_deps gcc g++ gfortran \
    musl-dev python3-dev
ln -s /usr/include/locale.h /usr/include/xlocale.h

pip install --no-cache-dir numpy==1.17.0
pip install --no-cache-dir psycopg2==2.8.3
pip install --no-cache-dir numpy-quaternion

rm /usr/include/xlocale.h
apk del .build_deps
