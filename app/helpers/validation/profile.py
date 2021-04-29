# -*- coding: utf-8 -*-
import logging

import geojson
from flask import abort
from shapely.geometry import shape

from app import make_error_msg
from app.helpers.profile_helpers import PROFILE_MAX_AMOUNT_POINTS, PROFILE_DEFAULT_AMOUNT_POINTS
from app.helpers.validation import srs_guesser

logger = logging.getLogger(__name__)


def read_linestring(request_object):
    # param geom, list of coordinates defining the line on which we want a profile
    linestring = None
    geom = None
    geom_to_shape = None
    if 'geom' in request_object.args:
        linestring = request_object.args.get('geom')
    elif request_object.is_json and len(request_object.get_data(as_text=True)) > 0:
        linestring = request_object.get_data()  # read as text
    if not linestring:
        abort(400, "No 'geom' given, cannot create a profile without coordinates")
    try:
        geom = geojson.loads(linestring, object_hook=geojson.GeoJSON.to_instance)
    except ValueError as e:
        logger.exception(e)
        abort(400, "Error loading geometry in JSON string")
    try:
        geom_to_shape = shape(geom)
    # pylint: disable=broad-except
    except Exception as e:
        logger.exception(e)
        abort(400, "Error converting JSON to Shape")
    try:
        geom_to_shape.is_valid
    # pylint: disable=broad-except
    except Exception:
        abort(400, "Invalid Linestring syntax")
    if len(geom_to_shape.coords) > PROFILE_MAX_AMOUNT_POINTS:
        abort(
            413,
            "Request Geometry contains too many points. Maximum number of points allowed: {}, "
            "found {}".format(PROFILE_MAX_AMOUNT_POINTS, len(geom_to_shape.coords))
        )
    return geom_to_shape


def read_number_points(request_object):
    # number of points wanted in the final profile.
    if 'nbPoints' in request_object.args:
        nb_points = request_object.args.get('nbPoints')
    elif 'nb_points' in request_object.args:
        nb_points = request_object.args.get('nb_points')
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
            "Please provide a numerical value for the parameter 'NbPoints'/'nb_points'" +
            " smaller than {}".format(PROFILE_MAX_AMOUNT_POINTS)
        )
    return nb_points


def read_is_custom_nb_points(request_object):
    # number of points wanted in the final profile.
    return 'nbPoints' in request_object.args or 'nb_points' in request_object.args


def read_spatial_reference(request_object, linestring):
    # param sr (or projection, sr meaning spatial reference), which Swiss projection to use.
    # Possible values are expressed in int, so value for EPSG:2056 (LV95) is 2056
    # and value for EPSG:21781 (LV03) is 21781. If this param is not present, it will be guessed
    # from the coordinates present in the param geom
    if 'sr' in request_object.args:
        spatial_reference = int(request_object.args.get('sr'))
    elif 'projection' in request_object.args:
        spatial_reference = int(request_object.args.get('projection'))
    else:
        sr = srs_guesser(linestring)
        if sr is None:
            abort(make_error_msg(400, "No 'sr' given and cannot be guessed from 'geom'"))
        spatial_reference = sr

    if spatial_reference not in (21781, 2056):
        abort(
            400,
            "Please provide a valid number for the spatial reference system model 21781 or 2056"
        )
    return spatial_reference


def read_offset(request_object):
    # param offset, used for smoothing. define how many coordinates should be included
    # in the window used for smoothing. If value is zero smoothing is disabled.
    offset = 3
    if 'offset' in request_object.args:
        offset = request_object.args.get('offset')
        if offset.isdigit():
            offset = int(offset)
        else:
            abort(400, "Please provide a numerical value for the parameter 'offset'")
    return offset
