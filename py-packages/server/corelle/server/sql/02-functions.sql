/*
Functions to rotate geometries directly in PostGIS. This allows Corelle plate rotations
to be applied to any geometry in the database. This requires plate geometries to be pre-cached
in the database for each time step and plate ID.
*/

CREATE OR REPLACE FUNCTION corelle.rotate_geometry(geom geometry, quaternion numeric[])
RETURNS geometry
AS $$
DECLARE
  cart numeric[];
  rotated numeric[];
BEGIN
  IF ST_GeometryType(geom) = 'ST_Point' THEN
    cart := sph2cart(geom);
    rotated := corelle.rotate_point(cart, quaternion);
    RETURN cart2sph(rotated);
  ELSIF ST_GeometryType(geom) = 'ST_MultiPoint' THEN
    RETURN ST_Collect(ARRAY(
      SELECT corelle.rotate_geometry(point, quaternion)
      FROM ST_DumpPoints(geom)
    ));
  ELSIF ST_GeometryType(geom) = 'ST_LineString' THEN
    RETURN ST_MakeLine(ARRAY(
      SELECT corelle.rotate_geometry(point, quaternion)
      FROM ST_DumpPoints(geom)
    ));
  ELSIF ST_GeometryType(geom) = 'ST_MultiLineString' THEN
    RETURN ST_Collect(ARRAY(
      SELECT corelle.rotate_geometry(line, quaternion)
      FROM ST_Dump(geom)
    ));
  ELSIF ST_GeometryType(geom) = 'ST_Polygon' THEN
    RETURN ST_MakePolygon(corelle.rotate_geometry(ST_ExteriorRing(geom), quaternion), ARRAY(
      SELECT corelle.rotate_geometry(ring, quaternion)
      FROM ST_DumpRings(geom)
    ));
  ELSIF ST_GeometryType(geom) = 'ST_MultiPolygon' THEN
    RETURN ST_Collect(ARRAY(
      SELECT corelle.rotate_geometry(polygon, quaternion)
      FROM ST_Dump(geom)
    ));
  ELSE
    RAISE EXCEPTION 'Unsupported geometry type: %', ST_GeometryType(geom);
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION corelle.rotate_point(point geometry, quaternion numeric[])
RETURNS geometry AS $$
DECLARE
  q0 numeric := quaternion[1];
  q1 numeric := quaternion[2];
  q2 numeric := quaternion[3];
  q3 numeric := quaternion[4];
  cart numeric := corelle.sph2cart(point);
  x numeric := cart[1];
  y numeric := cart[2];
  z numeric := cart[3];
  x2 numeric;
  y2 numeric;
  z2 numeric;
  w2 numeric;
  xy numeric;
  xz numeric;
  yz numeric;
  wx numeric;
  wy numeric;
  wz numeric;
BEGIN
  x2 := q0 * q0;
  y2 := q1 * q1;
  z2 := q2 * q2;
  w2 := q3 * q3;
  xy := q0 * q1;
  xz := q0 * q2;
  yz := q1 * q2;
  wx := q3 * q0;
  wy := q3 * q1;
  wz := q3 * q2;
  RETURN corelle.cart2sph(
    (x2 + y2 - z2 - w2) * x + 2 * (xy - wz) * y + 2 * (xz + wy) * z,
    (x2 - y2 + z2 - w2) * y + 2 * (xy + wz) * x + 2 * (yz - wx) * z,
    (x2 - y2 - z2 + w2) * z + 2 * (xz - wy) * x + 2 * (yz + wx) * y
  );
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION corelle.sph2cart(point geometry)
RETURNS numeric[] AS $$
DECLARE
  lat numeric := ST_Y(point);
  lon numeric := ST_X(point);
  r numeric := coalesce(ST_Z(point), 1);
BEGIN
  RETURN ARRAY[
    r * cos(lat) * cos(lon),
    r * cos(lat) * sin(lon),
    r * sin(lat)
  ];
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;


CREATE OR REPLACE FUNCTION corelle.cart2sph(x numeric, y numeric, z numeric)
RETURNS geometry
AS $$
DECLARE
  r numeric := sqrt(x * x + y * y + z * z);
  lat numeric := asin(z / r);
  lon numeric := atan2(y, x);
BEGIN
  IF r = 1 THEN
    RETURN ST_SetSRID(ST_MakePoint(lon, lat), 4326);
  ELSE
    RETURN ST_SetSRID(ST_MakePoint(lon, lat, r), 4326);
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;