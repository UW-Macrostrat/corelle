all: install

.PHONY: install

install:
	pip install -r requirements.txt
	pip install -e .
