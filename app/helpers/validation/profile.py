# -*- coding: utf-8 -*-
import logging

import geojson
from shapely.errors import GEOSException
from shapely.geometry import shape

from flask import abort
from flask import request

from app.helpers.profile_helpers import PROFILE_MAX_AMOUNT_POINTS
from app.helpers.validation import srs_guesser
from app.helpers.validation import validate_sr
from app.settings import strtobool

logger = logging.getLogger(__name__)
max_content_length = 32 * 1024 * 1024  # 32MB

PROFILE_VALID_GEOMETRY_TYPES = ['LineString', 'Point']


def get_args():
    args = dict(request.args)
    if request.method == 'POST':
        if request.content_type != "application/x-www-form-urlencoded" and not request.is_json:
            abort(415, f'{request.content_type} non allowed')
        if request.content_type == "application/x-www-form-urlencoded":
            args.update(request.form)
    return args


def read_linestring(args):
    # param geom, list of coordinates defining the line on which we want a profile
    linestring = None
    geom = None
    geom_to_shape = None
    if 'geom' in args:
        linestring = args.get('geom')
    elif request.method == 'POST' and request.is_json:
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
    except GEOSException as e:
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


def read_number_points(args):
    # number of points wanted in the final profile.
    if 'nbPoints' in args:
        nb_points = args['nbPoints']
    elif 'nb_points' in args:
        nb_points = args['nb_points']
    else:
        nb_points = None

    if nb_points is not None:
        try:
            nb_points = int(nb_points)
        except ValueError:
            abort(400, "Please provide a numerical value for the parameter 'NbPoints'/'nb_points'")

        if nb_points <= 1:
            abort(
                400,
                "Please provide a numerical value for the parameter 'NbPoints'/'nb_points' greater "
                "or equal to 2"
            )
        if nb_points > PROFILE_MAX_AMOUNT_POINTS:
            abort(
                400,
                "Please provide a numerical value for the parameter 'NbPoints'/'nb_points'"
                f" smaller than {PROFILE_MAX_AMOUNT_POINTS}"
            )
    return nb_points


def read_spatial_reference(linestring, args):
    # param sr (or projection, sr meaning spatial reference), which Swiss projection to use.
    # Possible values are expressed in int, so value for EPSG:2056 (LV95) is 2056
    # and value for EPSG:21781 (LV03) is 21781. If this param is not present, it will be guessed
    # from the coordinates present in the param geom
    if 'sr' in args:
        spatial_reference = int(args.get('sr'))
    elif 'projection' in args:
        spatial_reference = int(args.get('projection'))
    else:
        sr = srs_guesser(linestring)
        if sr is None:
            abort(400, "No 'sr' given and cannot be guessed from 'geom'")
        spatial_reference = sr

    validate_sr(spatial_reference)
    return spatial_reference


def read_offset(args):
    # param offset, used for smoothing. define how many coordinates should be included
    # in the window used for smoothing. If value is zero smoothing is disabled.
    offset = 0
    if 'offset' in args:
        offset = args.get('offset')
        if offset.isdigit():
            offset = int(offset)
        else:
            abort(400, "Please provide a numerical value for the parameter 'offset'")
    return offset


def read_only_requested_points(args):
    if 'only_requested_points' in args:
        try:
            only_requested_points = strtobool(args.get('only_requested_points'))
        except ValueError as error:
            logger.error('Invalid value for "only_requested_points" argument: %s', error)
            abort(400, f'Invalid value for "only_requested_points" argument: {error}')
    else:
        only_requested_points = False
    return only_requested_points


def read_smart_filling(args):
    if 'smart_filling' in args:
        try:
            smart_filling = strtobool(args.get('smart_filling'))
        except ValueError as error:
            logger.error('Invalid value for "smart_filling" argument: %s', error)
            abort(400, f'Invalid value for "smart_filling" argument: {error}')
    else:
        smart_filling = False
    return smart_filling


def read_distinct_points(args):
    if 'distinct_points' in args:
        try:
            keep_points = strtobool(args.get('distinct_points'))
        except ValueError as error:
            logger.error('Invalid value for "distinct_points" argument: %s', error)
            abort(400, f'Invalid value for "distinct_points" argument: {error}')
    else:
        keep_points = False
    return keep_points
