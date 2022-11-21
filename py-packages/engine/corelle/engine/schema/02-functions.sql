-- drop outdated function signatures
DROP FUNCTION IF EXISTS corelle.rotate_geometry(geometry, numeric[]);
DROP FUNCTION IF EXISTS corelle.rotate_geometry_pointwise(geometry, numeric[]);
DROP FUNCTION IF EXISTS corelle.build_proj_string(numeric[]);
DROP FUNCTION IF EXISTS corelle.rotate_geometry(geometry, numeric[]);
DROP FUNCTION IF EXISTS corelle.rotate_geometry_pointwise(geometry, numeric[]);
DROP FUNCTION IF EXISTS corelle.rotate_point(geometry, numeric[]);
DROP FUNCTION IF EXISTS corelle.quaternion_multiply(numeric[], numeric[]);
DROP FUNCTION IF EXISTS corelle.sph2cart(geometry);
DROP FUNCTION IF EXISTS corelle.cart2sph(numeric, numeric, numeric);
DROP FUNCTION IF EXISTS corelle.quaternion_to_euler(numeric[]);
DROP FUNCTION IF EXISTS corelle.euler_to_quaternion(geometry, numeric);
DROP FUNCTION IF EXISTS corelle.build_proj_string(numeric[]);
DROP FUNCTION IF EXISTS corelle.radians(numeric);
DROP FUNCTION IF EXISTS corelle.degrees(numeric);
DROP FUNCTION IF EXISTS corelle.invert_rotation(numeric[]);
DROP FUNCTION IF EXISTS corelle.rotate_geometry(geometry, integer, integer, integer);

/*
Functions to rotate geometries directly in PostGIS. This allows Corelle plate rotations
to be applied to any geometry in the database. This requires plate geometries to be pre-cached
in the database for each time step and plate ID.
*/
CREATE OR REPLACE FUNCTION corelle.rotate_geometry(geom geometry, quaternion double precision[])
RETURNS geometry
AS $$
DECLARE
  projection text := corelle.build_proj_string(quaternion);
BEGIN
  RETURN ST_SetSRID(ST_Transform(geom, projection), 4326);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

/**
Builds a projection string from a quaternion. This is the core of Corelle's on-database
rotation functionality.
*/
CREATE OR REPLACE FUNCTION corelle.build_proj_string(quaternion double precision[])
RETURNS text AS $$
DECLARE
  new_pole double precision[];
  lat_p double precision;
  lon_p double precision;
  lon_0 double precision;
  pz double precision;
  half_angle double precision;
  lon_s double precision;
  twist_q_w double precision;
BEGIN

  new_pole := corelle.quaternion_multiply(
    ARRAY[-quaternion[4], quaternion[3], -quaternion[2], quaternion[1]],
    corelle.invert_rotation(quaternion)
  );

  -- Make sure our latitude is never out of range
  pz := greatest(least(new_pole[4], 1::double precision), -1::double precision);
  lon_p := atan2(new_pole[3], new_pole[2]);
  lat_p := asin(pz);

  -- Pole rotation angle
  half_angle := -0.5*acos(pz);
  lon_s := lon_p + 0.5*pi();

  -- Get rotation component around new pole (the "twist")
  -- The z component is always 0
  twist_q_w := (
      quaternion[1] * cos(half_angle)
      - quaternion[2] * cos(lon_s) * sin(half_angle)
      - quaternion[3] * sin(lon_s) * sin(half_angle)
  );

  -- Get the twist angle around the new pole
  lon_0 := lon_p - 2 * acos(twist_q_w);

  RETURN format('+proj=ob_tran +o_proj=longlat +o_lon_p=%sr +o_lat_p=%sr +lon_0=%sr',
    lon_p,
    lat_p,
    lon_0
  );
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

/**
Naïve implementation of the quaternion rotation algorithm using PostGIS functions directly.
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
Hamilton product of two quaternions.
*/
CREATE OR REPLACE FUNCTION corelle.quaternion_multiply(q double precision[], r double precision[])
RETURNS double precision[]
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

CREATE OR REPLACE FUNCTION corelle.invert_rotation(quaternion double precision[])
RETURNS double precision[]
AS $$
BEGIN
  RETURN ARRAY[
    quaternion[1],
    -quaternion[2],
    -quaternion[3],
    -quaternion[4]
  ];
END;
$$ LANGUAGE plpgsql STABLE;

/* Rotate a geometry and clip to a bounding plate polygon */
CREATE OR REPLACE FUNCTION corelle.rotate_geometry(
  geom geometry,
  model_id integer,
  plate_id integer,
  time_ma numeric,
  should_clip boolean DEFAULT true
)
RETURNS geometry
AS $$
DECLARE
  plate geometry;
  rotation double precision[];
  clipped geometry;
BEGIN

  -- get rotation at closest time step
  SELECT r.rotation
  FROM corelle.rotation_cache r
  WHERE model_id = model_id
    AND plate_id = plate_id
    AND t_step = time_ma::integer
  INTO rotation;

  IF time_ma != 0 AND rotation IS null THEN
    RETURN null;
  END IF;

  /* If we're not clipping, the operation is relatively simple, and also
    should be much faster. */
  IF NOT should_clip THEN
    IF time_ma = 0 THEN
      RETURN geom;
    END IF;
    RETURN corelle.rotate_geometry(geom, rotation);
  END IF;

  /* If we're clipping, we need more information */
  SELECT geom
  FROM corelle.plate_polygon
  WHERE model_id = model_id
    AND plate_id = plate_id
    AND coalesce(old_lim, 4000) >= time_ma
    AND coalesce(young_lim, 0) < time_ma
  INTO plate;

  IF plate IS NULL THEN
    RETURN NULL;
  END IF;

  IF NOT geom && plate THEN
    RETURN NULL;
  END IF;

  clipped := ST_Intersection(
    geom,
    plate
  );

  IF t_step = 0 THEN
    RETURN clipped;
  END IF;

  RETURN corelle.rotate_geometry(clipped, rotation);
END;
$$ LANGUAGE plpgsql STABLE;

