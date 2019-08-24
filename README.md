# Corelle

No-nonsense plate rotations, compatible with **GPlates**. This repository contains
an API server that can rotate points using multiple plate models, and a testing
web application that implements client-side rotations based on this platform.

## Installation

### Local development

A recent (>3.6) version of Python is required to run the backend code. A recent
version of Node.js is required to bundle the frontend. The Python module expects
to use the `postgresql:///plate-rotations` database by default, but this can be
easily changed using the `CORELLE_DB` environment variable.

To install the backend, run `make install` in this repository. The `corelle`
executable should become available on your path. `make init` imports models and
feature datasets. Then `corelle serve` starts the testing API server.

To build (and continuously watch) the frontend, run `make dev`.
A backend API server will be started and proxied.

### Installation with Docker

Simply install Docker and run `docker-compose up --build` in the root directory.

## Todo

- [x] Fix subtle math bugs!
- [ ] On-database cache of rotations (say, at 1 Ma increments?)
- [ ] Return pre-rotated feature datasets (rather than just modern versions)
- [ ] Materialized view for split feature datasets
- [ ] Allow feature datasets to be listed
- [ ] Create a dockerized version
- [ ] Polish the frontend demo

## API Reference

### Get valid models

Returns a list of available models
```
/api/model
```

### Rotate a point

Pass points as a URLEncoded, space-separated list of comma-separated lon-lat pairs.
E.g. `20,-20 10,10` to rotate two points becomes
```
/api/point?model=Seton2012&data=20,-20%2010,10&time=40
```

### Rotation primitives

This route gives you the axis-angle or quaternion representation of plate rotations
at the specified time, for client-side rotation of points.

#### All rotations defined by the model

```
/api/rotate?time=10&model=Seton2012&quaternion=true
```

#### Rotation for a specific plate

```
/api/rotate?time=10&model=Seton2012&plate_id=quaternion=true
```

#### Return formats

##### Axis-angle

```json
{
  "axis": [
      0.027206502237792123,
      0.013804853692062557,
      -0.03262231893894808
  ],
  "angle": 0.08936020386653408,
  "plate_id": 311
}
```

##### Quaternion

```json
{
  "quaternion": [
      0.9990020102870522,
      0.027206502237792123,
      0.013804853692062557,
      -0.03262231893894808
  ],
  "plate_id": 311
}
```

### Features for rotation

For right now, features are not returned pre-rotated, but this capability will
be added to the API. Instead, features are returned as-is, with
`plate_id`, `old_lim`, and `young_lim` properties so they can be rotated client-side.

#### A named feature dataset

Arbitrary feature datasets (imported in advance on the backend).
The datasets are returned split on plate boundaries and  so they can be
rotated on the client side.
The example below fetches the `ne_110m_land` dataset.

```
/api/feature/ne_110m_land?model=Seton2012
```

TODO: allow listing of all named feature datasets.

#### Modern plate polygons

This route returns the plate polygons features themselves.

```
/api/plates?model=Seton2012
```
