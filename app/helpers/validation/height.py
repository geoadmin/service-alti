# -*- coding: utf-8 -*-

from flask import abort

from app.helpers.helpers import float_raise_nan


def validate_lon_lat(lon, lat):
    if lon is None:
        abort(400, "Missing parameter 'easting'/'lon'")
    try:
        lon = float_raise_nan(lon)
    except ValueError:
        abort(400, "Please provide numerical values for the parameter 'easting'/'lon'")

    if lat is None:
        abort(400, "Missing parameter 'northing'/'lat'")
    try:
        lat = float_raise_nan(lat)
    except ValueError:
        abort(400, "Please provide numerical values for the parameter 'northing'/'lat'")

    return lon, lat
