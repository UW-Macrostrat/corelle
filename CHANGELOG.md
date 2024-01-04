# Changelog

## [2.2.0] - 2024-01-04

- Update application for Python 3.11
- Update dependencies including SQLAlchemy 2

## [2.0.0]

- Switch dependency management to Poetry
- Break into submodules

## [Unknown]

- New [notebooks](notebooks) showing
  [usage in Python](notebooks/Corelle-Basic-Usage.ipynb) and building towards
  [paleolatitude tracers](notebooks/Corelle-Paleolatitude.ipynb).


## [1.1.0] - 2021-04-16

- Added a `/reconstruct` service that mirrors Macrostrat's legacy endpoint
- Switch dependency management to Poetry

## [1.0.4] - 2020-09-14

- `old_lim` and `young_lim` for plate polygons are now defaulted to the model
  `min_age` and `max_age`.

## [1.0.0] - 2020-08-15

- Created the `@macrostrat/corelle` client-side library.
- Improved Typescript definitions throughout the app.
- First demo of a [client-side application](https://davenquinn.com/viz/corelle-demo-pbdb/)
  using external features.

## [Preliminary] - May 2019 - August 2020

- Initial version of the app
- Conversion to Docker development strategy
