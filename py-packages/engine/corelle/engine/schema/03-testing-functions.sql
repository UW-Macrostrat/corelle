/** Drop old function signatures */
DROP FUNCTION IF EXISTS corelle.rotate_geometry_pointwise(geometry, numeric[]);
DROP FUNCTION IF EXISTS corelle.rotate_point(geometry, numeric[]);
DROP FUNCTION IF EXISTS corelle.sph2cart(geometry);
DROP FUNCTION IF EXISTS corelle.cart2sph(numeric, numeric, numeric);
DROP FUNCTION IF EXISTS corelle.quaternion_to_euler(numeric[]);
DROP FUNCTION IF EXISTS corelle.euler_to_quaternion(geometry, numeric);
DROP FUNCTION IF EXISTS corelle.radians(numeric);
DROP FUNCTION IF EXISTS corelle.degrees(numeric);

/**
Naïve implementation of the quaternion rotation algorithm using PostGIS functions directly.

This is quite slow compared to using PROJ directly. It is included here for reference and
testing purposes.
*/
CREATE OR REPLACE FUNCTION corelle.rotate_geometry_pointwise(geom geometry, quaternion double precision[])
RETURNS geometry
AS $$
DECLARE
  result geometry;
  rings geometry[];
BEGIN
  IF ST_GeometryType(geom) = 'ST_Point' THEN
    RETURN corelle.rotate_point(geom, quaternion);
  ELSIF ST_GeometryType(geom) = 'ST_MultiPoint' THEN
    RETURN ST_Collect(ARRAY(
      SELECT corelle.rotate_geometry_pointwise(g.geom, quaternion)
      FROM ST_DumpPoints(geom) AS g
    ));
  ELSIF ST_GeometryType(geom) = 'ST_LineString' THEN
    RETURN ST_MakeLine(ARRAY(
      SELECT corelle.rotate_geometry_pointwise(g.geom, quaternion)
      FROM ST_DumpPoints(geom) AS g
    ));
  ELSIF ST_GeometryType(geom) = 'ST_MultiLineString' THEN
    RETURN ST_Collect(ARRAY(
      SELECT corelle.rotate_geometry_pointwise(g.geom, quaternion)
      FROM ST_Dump(geom) AS g
    ));
  ELSIF ST_GeometryType(geom) = 'ST_Polygon' THEN
    -- don't handle rings yet...
    -- Rotate interior rings
    rings := ARRAY(
      SELECT corelle.rotate_geometry_pointwise(ST_InteriorRingN(geom, r), quaternion)
      FROM generate_series(1, ST_NumInteriorRing(geom)) AS r
    );

    RETURN ST_MakePolygon(corelle.rotate_geometry_pointwise(ST_ExteriorRing(geom), quaternion), rings);
  ELSIF ST_GeometryType(geom) = 'ST_MultiPolygon' THEN
    RETURN ST_Collect(ARRAY(
      SELECT corelle.rotate_geometry_pointwise(g.geom, quaternion)
      FROM ST_Dump(geom) AS g
    ));
  ELSE
    RAISE EXCEPTION 'Unsupported geometry type: %', ST_GeometryType(geom);
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION corelle.rotate_point(point geometry, quaternion double precision[])
RETURNS geometry AS $$
DECLARE
  pt double precision[] := corelle.sph2cart(point);
  q_conj double precision[];
  q_res double precision[];
  r double precision[];
BEGIN
  q_conj := ARRAY[
    quaternion[1],
    -quaternion[2],
    -quaternion[3],
    -quaternion[4]
  ];

  r := ARRAY[0, pt[1], pt[2], pt[3]];

  q_res := corelle.quaternion_multiply(
    corelle.quaternion_multiply(quaternion, r),
    q_conj
  );

  RETURN corelle.cart2sph(
    q_res[2],
    q_res[3],
    q_res[4]
  );
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

/**
* UTILITIES for converting between spherical and cartesian coordinates.
* These are primarily used for testing purposes.
*/
CREATE OR REPLACE FUNCTION corelle.sph2cart(point geometry)
RETURNS double precision[] AS $$
DECLARE
  lon double precision := corelle.radians(ST_X(point));
  lat double precision := corelle.radians(ST_Y(point));
  r double precision := coalesce(ST_Z(point), 1);
BEGIN
  RETURN ARRAY[
    r * cos(lat) * cos(lon),
    r * cos(lat) * sin(lon),
    r * sin(lat)
  ];
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;


CREATE OR REPLACE FUNCTION corelle.cart2sph(x double precision, y double precision, z double precision)
RETURNS geometry
AS $$
DECLARE
  r double precision := sqrt(x * x + y * y + z * z);
  lat double precision := corelle.degrees(asin(z / r));
  lon double precision := corelle.degrees(atan2(y, x));
BEGIN
  IF abs(r-1) < 0.0000001 THEN
    RETURN ST_SetSRID(ST_MakePoint(lon, lat), 4326);
  ELSE
    RETURN ST_SetSRID(ST_MakePoint(lon, lat, r), 4326);
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION corelle.quaternion_to_euler(q double precision[])
RETURNS double precision[] AS $$
DECLARE
  w double precision := q[1];
  x double precision := q[2];
  y double precision := q[3];
  z double precision := q[4];
  angle double precision := 2 * acos(w);
  scalar double precision := sin(angle / 2);
  lat double precision;
  lon double precision;
BEGIN
  IF scalar = 0 THEN
    RETURN null;
  ELSE
    lat := asin(z/scalar);
    lon := atan2(y/scalar, x/scalar);
    RETURN ARRAY[lon, lat, angle];
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION corelle.euler_to_quaternion(pole geometry, angle double precision)
RETURNS double precision[] AS $$
DECLARE
  half_angle double precision := corelle.radians(angle) / 2;
  scalar double precision := sin(half_angle);
  v double precision[] := corelle.sph2cart(pole);
BEGIN
  RETURN ARRAY[
    cos(half_angle),
    v[1] * scalar,
    v[2] * scalar,
    v[3] * scalar
  ];
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

/* Convert to radians */
CREATE OR REPLACE FUNCTION corelle.radians(degrees double precision)
RETURNS double precision AS $$
BEGIN
  RETURN degrees * pi() / 180;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

/* Convert to degrees */
CREATE OR REPLACE FUNCTION corelle.degrees(radians double precision)
RETURNS double precision AS $$
DECLARE
  uncorrected double precision := radians * 180 / pi();
BEGIN
  -- Return data in the right quadrant
  IF uncorrected < -180 THEN
    RETURN uncorrected + 360;
  ELSE
    RETURN uncorrected;
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;
