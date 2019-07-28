all: install

.PHONY: install init update_functions

install:
	pip install -r requirements.txt
	pip install -e .

init:
	-createdb plate-rotations
	plates init --drop
	plates import "PalaeoPlates" \
		--fields data/eglington-fields.yaml \
		data/eglington/PlatePolygons2016All.json \
		data/eglington/T_Rot_Model_PalaeoPlates_2019_20190302_experiment.rot
	plates import "Seton2012" \
		--fields data/seton-fields.yaml \
		data/seton_2012.geojson \
		data/seton_2012.rot
	plates import "Wright2013" \
		--fields data/wright-fields.yaml \
		data/wright_plates.geojson \
		data/wright_2013.rot
	plates import "Scotese" \
		--fields data/scotese-fields.yaml \
		data/scotese.geojson \
		data/scotese.rot

update_functions:
	cat corelle/sql/02-functions.sql | psql plate-rotations
