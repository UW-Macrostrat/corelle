all: install

.PHONY: install init update_functions test dev features

install:
	poetry install

init:
	-createdb plate-rotations
	poetry run corelle init --drop
	poetry run bin/load-models

update_functions:
	cat corelle/sql/02-functions.sql | psql plate-rotations

baseurl := https://raw.githubusercontent.com/martynafford/natural-earth-geojson/master

features: bin/load-features
	poetry run bin/load-features --redo plate-rotations

test:
	poetry run bin/run-tests

dev:
	cd frontend && poetry run npm run dev
