# Corelle

No-nonsense plate rotations, compatible with **GPlates**. This repository contains
an API server that can rotate points using multiple plate models, and a testing
web application that implements client-side rotations based on this platform.

## Installation

A recent (>3.6) version of Python is required to run the backend code.

## Todo

- [ ] Fix subtle math bugs!
- [ ] On-database cache of rotations (say, at 1 Ma increments?)
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

## Rotated features

### A named feature dataset

These feature datasets must be imported in advance; they are returned split on plate
boundaries and with `plate_id`, `old_lim`, and `young_lim` properties so they can be
rotated on the client side. The example below fetches the `ne_110m_land` dataset.

```
/api/feature/ne_110m_land?model=Seton2012
```

#### Modern plate polygons

This route feature returns the plate polygons themselves.

```
/api/plates?model=Seton2012
```
