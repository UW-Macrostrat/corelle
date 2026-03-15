all: install

.PHONY: install init update_functions test dev features publish

DOCKER_IMAGE_VERSION := 1.0.0

# We centrally manage the version of Docker images for simplicity at this point
# We should get a better CI architecture eventually, or move the actual API
# definition to the Macrostrat repository.
publish:
	# Ensure we have an empty index
	git diff-index --quiet HEAD --
	git tag -a v$(DOCKER_IMAGE_VERSION) -m "Version $(DOCKER_IMAGE_VERSION)"
	git push origin tag v$(DOCKER_IMAGE_VERSION)

lock:
	bin/update-packages

install:
	make lock
	poetry install

test-docker:
	bin/test-docker

test:
	poetry run bin/run-tests

dev:
	cd frontend && poetry run npm run dev

# Outdated functions

update_functions:
	cat py-packages/engine/corelle/engine/schema/*-functions.sql | psql plate-rotations

baseurl := https://raw.githubusercontent.com/martynafford/natural-earth-geojson/master

features: bin/load-features
	poetry run bin/load-features --redo plate-rotations

init:
	-createdb plate-rotations
	poetry run corelle init --drop
	poetry run bin/load-models
