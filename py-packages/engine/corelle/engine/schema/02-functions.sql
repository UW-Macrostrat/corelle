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

CREATE OR REPLACE FUNCTION corelle.build_proj_string(quaternion numeric[])
RETURNS text AS $$
DECLARE
  euler numeric[];
  lon numeric;
  lat numeric;
  angle numeric;
BEGIN
  euler := corelle.quaternion_to_euler(quaternion);
  IF euler IS null THEN
    RETURN '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs';
  END IF;
  --new_pole = corelle.rotate_point(ST_MakePoint(0, 90), quaternion);
  RETURN '+proj=ob_tran +o_proj=longlat +o_lon_c=0 +o_lat_c=0 +o_alpha=5';
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
