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

baseurl := https://raw.githubusercontent.com/martynafford/natural-earth-geojson/master

load_features:
	-mkdir temp
	curl -o temp/ne_110m_land.json \
		$(baseurl)/110m/physical/ne_110m_land.json
	curl -o temp/ne_50m_land.json \
		$(baseurl)/50m/physical/ne_50m_land.json
	curl -o temp/macrostrat_columns.json "https://macrostrat.org/api/v2/columns?all&format=geojson"
	cat temp/macrostrat_columns.json | jq .success.data > temp/macrostrat_columns2.json
	plates import-features --overwrite ne_110m_land temp/ne_110m_land.json
	plates import-features --overwrite ne_50m_land temp/ne_50m_land.json
	plates import-features --overwrite macrostrat_columns temp/macrostrat_columns2.json
	rm -rf temp
