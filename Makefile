all: install

.PHONY: install

install:
	pip install -r requirements.txt
	pip install -e .

create:
	-createdb plate-rotations
	plates init
