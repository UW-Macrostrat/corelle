all: install

.PHONY: install init

install:
	pip install -r requirements.txt
	pip install -e .

init:
	-createdb plate-rotations
	plates init --drop
	plates import "PalaeoPlates" \
		data/eglington/PlatePolygons2016All.json \
		data/eglington/T_Rot_Model_PalaeoPlates_2019_20190302_experiment.rot
