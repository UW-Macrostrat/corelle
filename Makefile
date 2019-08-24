all: install

.PHONY: install init update_functions test dev

install:
	pip install -r requirements.txt
	pip install -e .

init:
	-createdb plate-rotations
	corelle init --drop
	corelle import "PalaeoPlates" \
		--fields data/eglington-fields.yaml \
		data/eglington/PlatePolygons2016All.json \
		data/eglington/T_Rot_Model_PalaeoPlates_2019_20190302_experiment.rot
	corelle import "Seton2012" \
		--fields data/seton-fields.yaml \
		data/seton_2012.geojson \
		data/Seton_etal_ESR2012_2012.1.rot
	corelle import "Wright2013" \
		--fields data/wright-fields.yaml \
		data/wright_plates.geojson \
		data/wright_2013.rot
	corelle import "Scotese" \
		--fields data/scotese-fields.yaml \
		data/scotese.geojson \
		data/scotese.rot

update_functions:
	cat corelle/sql/02-functions.sql | psql plate-rotations

baseurl := https://raw.githubusercontent.com/martynafford/natural-earth-geojson/master

load_features: bin/load-features
	./$^

test:
	bin/run-tests

dev:
	cd frontend && npm run dev
