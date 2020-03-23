# -*- coding: utf-8 -*-

import math
from functools import partial
from shapely.ops import transform as shape_transform
from pyproj import Proj, transform as proj_transform


# float('NaN') does not raise an Exception. This function does.
def float_raise_nan(val):
    ret = float(val)
    if math.isnan(ret):
        raise ValueError('nan is not considered valid float')
    return ret


def filter_altitude(altitude, digits=1):
    """Returns the altitude given in parameter, rounded one decimal place"""
    if altitude is not None and altitude > 0.0:
        # 10cm accuracy is enough for altitudes
        return round(altitude, digits)
    else:
        return None


def filter_distance(distance, digits=1):
    """Returns the distance given in parameter rounded one decimal place"""
    # 10cm accuracy is enough for distances
    return round(distance, digits)


def filter_coordinate(coordinate, digits=3):
    """Returns the coordinate given in parameter, rounder three decimal places"""
    # 1mm accuracy is enough for coordinates
    return round(coordinate, digits)


def get_proj_from_srid(srid):
    return Proj(init='EPSG:{}'.format(srid))


def transform_coordinate(coords, srid_from, srid_to):
    proj_in = get_proj_from_srid(srid_from)
    proj_out = get_proj_from_srid(srid_to)
    return proj_transform(proj_in, proj_out, coords[0], coords[1])


def transform_shape(geom, srid_from, srid_to):
    if srid_from == srid_to:
        return geom

    proj_in = get_proj_from_srid(srid_from)
    proj_out = get_proj_from_srid(srid_to)

    projection_func = partial(proj_transform, proj_in, proj_out)

    return shape_transform(projection_func, geom)
