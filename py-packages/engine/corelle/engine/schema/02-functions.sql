/*
Functions to rotate geometries directly in PostGIS. This allows Corelle plate rotations
to be applied to any geometry in the database. This requires plate geometries to be pre-cached
in the database for each time step and plate ID.
*/

CREATE OR REPLACE FUNCTION corelle.rotate_geometry(geom geometry, quaternion numeric[])
RETURNS geometry
AS $$
DECLARE
  projection text := corelle.build_proj_string(quaternion);
BEGIN
  RETURN ST_Transform(geom, projection);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

/**
Naïve implementation of the quaternion rotation algorithm using PostGIS functions directly.
*/
CREATE OR REPLACE FUNCTION corelle.rotate_geometry_pointwise(geom geometry, quaternion numeric[])
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

CREATE OR REPLACE FUNCTION corelle.quaternion_to_euler(q numeric[])
RETURNS numeric[] AS $$
DECLARE
  w numeric := q[1];
  x numeric := q[2];
  y numeric := q[3];
  z numeric := q[4];
  angle numeric := 2 * acos(w);
  scalar numeric := sin(angle / 2);
  lat numeric;
  lon numeric;
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

CREATE OR REPLACE FUNCTION corelle.euler_to_quaternion(pole geometry, angle numeric)
RETURNS numeric[] AS $$
DECLARE
  half_angle numeric := corelle.radians(angle) / 2;
  scalar numeric := sin(half_angle);
  v numeric[] := corelle.sph2cart(pole);
BEGIN
  RETURN ARRAY[
    cos(half_angle),
    v[1] * scalar,
    v[2] * scalar,
    v[3] * scalar
  ];
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION corelle.build_proj_string(quaternion numeric[])
RETURNS text AS $$
DECLARE
  new_pole geometry;
  swing_q_inv numeric[];
  twist_q_w numeric;
  twist_angle numeric;
  lon_0 numeric;
BEGIN

  -- Rotate the north pole by the quaternion
  q_conj := ARRAY[
    quaternion[1],
    -quaternion[2],
    -quaternion[3],
    -quaternion[4]
  ];

  r := ARRAY[0, 0, 0, 1];

  new_pole := corelle.quaternion_multiply(
    corelle.quaternion_multiply(quaternion, r),
    q_conj
  );

  half_angle := acos(new_pole[1]);
  scalar numeric := sin(half_angle);
  v numeric[] := corelle.sph2cart(pole);

  -- get the new pole vector by cross product
  pole := ARRAY[
    new_pole[2],
    new_pole[1],
    0
  ];

  swing_q_inv := ARRAY[
    cos(half_angle),
    -v[1] * scalar,
    -v[2] * scalar,
    -v[3] * scalar
  ];
BEGIN
  RETURN ARRAY[
    cos(half_angle),
    v[1] * scalar,
    v[2] * scalar,
    v[3] * scalar
  ];

  RETURN corelle.cart2sph(
    q_res[2],
    q_res[3],
    q_res[4]
  );


  new_pole := corelle.rotate_point(ST_SetSRID(ST_MakePoint(0, 90), 4326), quaternion);

  swing_q_inv := corelle.euler_to_quaternion(
    ST_MakePoint(ST_X(new_pole) + 90, 0),
    (ST_Y(new_pole) - 90)::numeric
  );

  RAISE NOTICE 'new_pole: %', ST_AsText(new_pole);

  RAISE NOTICE 'swing_q_inv: %', swing_q_inv;

  twist_q_w := quaternion[1] * swing_q_inv[1]
              - quaternion[2] * swing_q_inv[2]
              - quaternion[3] * swing_q_inv[3]
              - quaternion[4] * swing_q_inv[4];

  RAISE NOTICE 'twist_q: %', twist_q_w;

  twist_angle := corelle.degrees(2 * acos(twist_q_w));

  lon_0 := ST_X(new_pole) - twist_angle;

  RETURN format('+proj=ob_tran +o_proj=longlat +o_lon_p=%s +o_lat_p=%s +lon_0=%s',
    ST_X(new_pole),
    ST_Y(new_pole),
    lon_0
  );
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

CREATE OR REPLACE FUNCTION corelle.invert_rotation(quaternion numeric[])
RETURNS numeric[]
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
  rotation numeric[];
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

-- Drop old function signatures
DROP FUNCTION IF EXISTS corelle.rotate_geometry(geometry, integer, integer, integer);
