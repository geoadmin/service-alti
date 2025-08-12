from shapely.geometry import Polygon

from flask import abort

from app.helpers.helpers import float_raise_nan
from app.settings import VALID_SRID

bboxes = {
    2056:
        (
            float_raise_nan(2385000),  # xmin: expanded to cover old and new
            float_raise_nan(974000),  # ymin: expanded to cover old and new
            float_raise_nan(2935000),  # xmax: expanded to cover old and new
            float_raise_nan(1404000)  # ymax: expanded to cover old and new
        ),
    21781:
        (
            float_raise_nan(385000),  # xmin: expanded to cover old and new
            float_raise_nan(-26000),  # ymin: expanded to cover old and new
            float_raise_nan(940000),  # xmax: expanded to cover old and new
            float_raise_nan(456000)  # ymax: expanded to cover old and new
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
