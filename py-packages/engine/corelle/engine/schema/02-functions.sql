/*
Functions to rotate geometries directly in PostGIS. This allows Corelle plate rotations
to be applied to any geometry in the database. This requires plate geometries to be pre-cached
in the database for each time step and plate ID.
*/

CREATE OR REPLACE FUNCTION corelle.rotate_geometry(geom geometry, quaternion numeric[])
RETURNS geometry
AS $$
DECLARE
  result geometry;
BEGIN
  IF ST_GeometryType(geom) = 'ST_Point' THEN
    RETURN corelle.rotate_point(geom, quaternion);
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
  pt numeric[] := corelle.sph2cart(point);
  q_conj numeric[];
  q_res numeric[];
  r numeric[];
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

CREATE OR REPLACE FUNCTION corelle.rotate_vector(vector numeric[], quaternion numeric[]) RETURNS numeric[] AS $$
DECLARE
  q_conj numeric[];
  q_res numeric[];
  r numeric[];
BEGIN
  q_conj := ARRAY[
    quaternion[1],
    -quaternion[2],
    -quaternion[3],
    -quaternion[4]
  ];

  r := ARRAY[0, vector[1], vector[2], vector[3]];

  q_res := corelle.quaternion_multiply(
    corelle.quaternion_multiply(quaternion, r),
    q_conj
  );

  RETURN ARRAY[q_res[2], q_res[3], q_res[4]];
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION corelle.quaternion_multiply(q numeric[], r numeric[])
RETURNS numeric[]
AS $$
BEGIN 
  RETURN ARRAY[
    r[1]*q[1]-r[2]*q[2]-r[3]*q[3]-r[4]*q[4],
    r[1]*q[2]+r[2]*q[1]-r[3]*q[4]+r[4]*q[3],
    r[1]*q[3]+r[2]*q[4]+r[3]*q[1]-r[4]*q[2],
    r[1]*q[4]-r[2]*q[3]+r[3]*q[2]+r[4]*q[1]
  ];
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;


CREATE OR REPLACE FUNCTION corelle.sph2cart(point geometry)
RETURNS numeric[] AS $$
DECLARE
  lon numeric := corelle.radians(ST_X(point));
  lat numeric := corelle.radians(ST_Y(point));
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
  lat numeric := corelle.degrees(asin(z / r));
  lon numeric := corelle.degrees(atan2(y, x));
BEGIN
  IF abs(r-1) < 0.0000001 THEN
    RETURN ST_SetSRID(ST_MakePoint(lon, lat), 4326);
  ELSE
    RETURN ST_SetSRID(ST_MakePoint(lon, lat, r), 4326);
  END IF;
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

/* Rotate a geometry and clip to a bounding plate polygon */
CREATE OR REPLACE FUNCTION corelle.rotate_geometry(
  geom geometry,
  model_id integer,
  plate_id integer,
  t_step integer
)
RETURNS geometry
AS $$
DECLARE
  plate geometry;
  rotation numeric[];
  clipped geometry;
BEGIN

  -- get rotation at closest time step
  SELECT rotation
  FROM corelle.rotation
  WHERE model_id = model_id
    AND plate_id = plate_id
    AND t_step = t_step
  INTO rotation;

  IF t_step != 0 AND rotation IS null THEN
    RETURN null;
  END IF;

  SELECT geom
  FROM corelle.plate_polygon
  WHERE model_id = model_id
    AND plate_id = plate_id
    AND coalesce(old_lim, 4000) >= t_step
    AND coalesce(young_lim, 0) < t_step
  INTO plate;

  IF plate IS NULL THEN
    RETURN NULL;
  END IF;

  IF NOT geom && plate THEN
    RETURN NULL;
  END IF;

  clipped := ST_Intersection(geom, plate);

  IF t_step = 0 THEN
    RETURN clipped;
  END IF;

  RETURN corelle.rotate_geometry(clipped, rotation);
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

