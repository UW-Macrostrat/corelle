all: install

.PHONY: install init update_functions test dev features

install:
	pip install -r requirements.txt
	pip install -e .

init:
	-createdb plate-rotations
	corelle init --drop
	bin/load-models

update_functions:
	cat corelle/sql/02-functions.sql | psql plate-rotations

baseurl := https://raw.githubusercontent.com/martynafford/natural-earth-geojson/master

features: bin/load-features
	bin/load-features --redo plate-rotations

test:
	bin/run-tests

dev:
	cd frontend && npm run dev
