# -*- coding: utf-8 -*-

from shapely.geometry import Polygon

from flask import abort

from app.helpers.helpers import float_raise_nan
from app.settings import VALID_SRID

bboxes = {
    2056:
        (
            float_raise_nan(2450000),
            float_raise_nan(1030000),
            float_raise_nan(2900000),
            float_raise_nan(1350000)
        ),
    21781:
        (
            float_raise_nan(450000),
            float_raise_nan(30000),
            float_raise_nan(900000),
            float_raise_nan(350000)
        )
}


def srs_guesser(geom):
    sr = None
    try:
        geom_type = geom.geom_type
    except ValueError:
        return sr

    if geom_type in ('Point', 'LineString'):
        for epsg, bbox in bboxes.items():
            dtm_poly = Polygon(
                [(bbox[0], bbox[1]), (bbox[2], bbox[1]), (bbox[2], bbox[3]), (bbox[0], bbox[3])]
            )
            if dtm_poly.contains(geom):
                sr = epsg
                break
    return sr


def validate_sr(sr):
    if sr not in VALID_SRID:
        abort(
            400,
            "Please provide a valid number for the spatial reference system model: "
            f"{', '.join(map(str, VALID_SRID))}"
        )
    return sr
