-- drop outdated function signatures
DROP FUNCTION IF EXISTS corelle.rotate_geometry(geometry, numeric[]);
DROP FUNCTION IF EXISTS corelle.rotate_geometry(geometry, integer, integer, integer);
DROP FUNCTION IF EXISTS corelle.build_proj_string(numeric[]);
DROP FUNCTION IF EXISTS corelle.quaternion_multiply(numeric[], numeric[]);
DROP FUNCTION IF EXISTS corelle.invert_rotation(numeric[]);
DROP FUNCTION IF EXISTS corelle.rotate_geometry(geometry, double precision[]);
DROP FUNCTION IF EXISTS corelle.rotate_geometry(geometry,integer,integer,numeric,boolean);

/*
Functions to rotate geometries directly in PostGIS. This allows Corelle plate rotations
to be applied to any geometry in the database. This requires plate geometries to be pre-cached
in the database for each time step and plate ID.
*/
CREATE OR REPLACE FUNCTION corelle.rotate_geometry(
  geom geometry,
  quaternion double precision[],
  wrap_lon numeric DEFAULT 0
)
RETURNS geometry
AS $$
DECLARE
  projection text := corelle.build_proj_string(quaternion);
  g1 geometry;
BEGIN
  return ST_SetSRID(ST_Transform(geom, projection), 4326);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION corelle.invert_rotation(quaternion double precision[])
RETURNS double precision[]
AS $$
  -- norm := sqrt(
  --   pow(quaternion[1],2) + pow(quaternion[2],2) +
  --   pow(quaternion[3],2) + pow(quaternion[4], 2)
  -- );

  SELECT ARRAY[
    quaternion[1],
    -quaternion[2],
    -quaternion[3],
    -quaternion[4]
  ] ;
$$ LANGUAGE sql IMMUTABLE STRICT;

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


/* Rotate a geometry and clip to a bounding plate polygon */
CREATE OR REPLACE FUNCTION corelle.rotate_geometry(
  geom geometry,
  _model_id integer,
  _plate_id integer,
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
  WHERE model_id = _model_id
    AND plate_id = _plate_id
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
  WHERE model_id = _model_id
    AND plate_id = _plate_id
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

  IF time_ma = 0 THEN
    RETURN clipped;
  END IF;

  RETURN corelle.rotate_geometry(clipped, rotation);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

DROP FUNCTION IF EXISTS corelle.build_proj_string(double precision[]);
DROP FUNCTION IF EXISTS corelle.build_proj_string(double precision[], text);
DROP FUNCTION IF EXISTS corelle.build_proj_string(double precision[], text, text);

/**
Builds a projection string from a quaternion. This is the core of Corelle's on-database
rotation functionality.

Big thanks to Duncan Agnew and the PROJ listserv for helping me figure out the right angular
representation to use here.
*/
CREATE OR REPLACE FUNCTION corelle.build_proj_string(
  quaternion double precision[],
  extra_params text DEFAULT '+o_proj=longlat',
  lon_adjustment numeric DEFAULT 0
)
RETURNS text AS $$
DECLARE
  new_pole double precision[];
  lat_p double precision;
  lon_p double precision;
  lon_0 double precision;
  norm double precision;
  twist_q_w double precision;
  twist_angle double precision;
BEGIN

  new_pole := corelle.quaternion_multiply(
    ARRAY[-quaternion[4], quaternion[3], -quaternion[2], quaternion[1]],
    corelle.invert_rotation(quaternion)
  );

  lon_p := atan2(new_pole[3], new_pole[2]);
  lat_p := asin(new_pole[4]);

  norm := sqrt(pow(quaternion[1],2) + pow(quaternion[4], 2));

  IF norm = 0 THEN
    twist_q_w := 1;
  ELSIF quaternion[4] < 0 THEN
    twist_q_w := -quaternion[1] / norm;
  ELSE
    twist_q_w := quaternion[1] / norm;
  END IF;

  twist_angle := 2 * acos(twist_q_w);

  lon_0 := lon_p - twist_angle;

  RETURN format('+proj=ob_tran +o_lon_p=%sr +o_lat_p=%sr +lon_0=%sr ' || extra_params, 
    lon_p,
    lat_p,
    lon_0
  );
END;
$$ LANGUAGE plpgsql IMMUTABLE;


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