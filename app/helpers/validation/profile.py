# -*- coding: utf-8 -*-
import logging

import geojson
from shapely.geometry import shape

from flask import abort
from flask import request

from app.helpers.profile_helpers import PROFILE_DEFAULT_AMOUNT_POINTS
from app.helpers.profile_helpers import PROFILE_MAX_AMOUNT_POINTS
from app.helpers.validation import srs_guesser

logger = logging.getLogger(__name__)
max_content_length = 32 * 1024 * 1024  # 32MB

PROFILE_VALID_GEOMETRY_TYPES = ['LineString', 'Point']


def read_linestring():
    # param geom, list of coordinates defining the line on which we want a profile
    linestring = None
    geom = None
    geom_to_shape = None
    if 'geom' in request.args:
        linestring = request.args.get('geom')
    elif request.method == 'POST':
        if not request.is_json:
            abort(415)
        if request.content_length and 0 < request.content_length < max_content_length:
            linestring = request.get_data(as_text=True)  # read as text

    if not linestring:
        abort(400, "No 'geom' given, cannot create a profile without coordinates")

    try:
        geom = geojson.loads(linestring, object_hook=geojson.GeoJSON.to_instance)
    except ValueError as e:
        logger.error('Invalid "geom" parameter, it is not geojson: %s', e)
        abort(400, "Invalid geom parameter, must be a GEOJSON")

    if geom.get('type') not in PROFILE_VALID_GEOMETRY_TYPES:
        abort(400, f"geom parameter must be a {'/'.join(PROFILE_VALID_GEOMETRY_TYPES)} GEOJSON")

    try:
        geom_to_shape = shape(geom)
    except ValueError as e:
        logger.error("Failed to transformed GEOJSON to shape: %s", e)
        abort(400, "Error converting GEOJSON to Shape")

    if not geom_to_shape.is_valid:
        abort(400, f"Invalid {geom['type']}")

    if len(geom_to_shape.coords) > PROFILE_MAX_AMOUNT_POINTS:
        abort(
            413,
            "Request Geometry contains too many points. Maximum number of points allowed: "
            f"{PROFILE_MAX_AMOUNT_POINTS}, found {len(geom_to_shape.coords)}"
        )
    return geom_to_shape


def read_number_points():
    # number of points wanted in the final profile.
    if 'nbPoints' in request.args:
        nb_points = request.args.get('nbPoints')
    elif 'nb_points' in request.args:
        nb_points = request.args.get('nb_points')
    else:
        nb_points = PROFILE_DEFAULT_AMOUNT_POINTS

    if (isinstance(nb_points, int) or nb_points.isdigit()) and int(nb_points) <= 1:
        abort(
            400,
            "Please provide a numerical value for the parameter 'NbPoints'/'nb_points' greater "
            "or equal to 2"
        )
    if (isinstance(nb_points, int) or
        nb_points.isdigit()) and int(nb_points) <= PROFILE_MAX_AMOUNT_POINTS:
        nb_points = int(nb_points)
    else:
        abort(
            400,
            "Please provide a numerical value for the parameter 'NbPoints'/'nb_points'"
            f" smaller than {PROFILE_MAX_AMOUNT_POINTS}"
        )
    return nb_points


def read_is_custom_nb_points():
    # number of points wanted in the final profile.
    return 'nbPoints' in request.args or 'nb_points' in request.args


def read_spatial_reference(linestring):
    # param sr (or projection, sr meaning spatial reference), which Swiss projection to use.
    # Possible values are expressed in int, so value for EPSG:2056 (LV95) is 2056
    # and value for EPSG:21781 (LV03) is 21781. If this param is not present, it will be guessed
    # from the coordinates present in the param geom
    if 'sr' in request.args:
        spatial_reference = int(request.args.get('sr'))
    elif 'projection' in request.args:
        spatial_reference = int(request.args.get('projection'))
    else:
        sr = srs_guesser(linestring)
        if sr is None:
            abort(400, "No 'sr' given and cannot be guessed from 'geom'")
        spatial_reference = sr

    if spatial_reference not in (21781, 2056):
        abort(
            400,
            "Please provide a valid number for the spatial reference system model 21781 or 2056"
        )
    return spatial_reference


def read_offset():
    # param offset, used for smoothing. define how many coordinates should be included
    # in the window used for smoothing. If value is zero smoothing is disabled.
    offset = 0
    if 'offset' in request.args:
        offset = request.args.get('offset')
        if offset.isdigit():
            offset = int(offset)
        else:
            abort(400, "Please provide a numerical value for the parameter 'offset'")
    return offset
