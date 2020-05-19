# -*- coding: utf-8 -*-

import math
import logging

# float('NaN') does not raise an Exception. This function does.
def float_raise_nan(val):
    ret = float(val)
    if math.isnan(ret):
        raise ValueError('nan is not considered valid float')
    return ret


def filter_altitude(altitude):
    """Returns the altitude given in parameter, rounded one decimal place"""
    if altitude is not None and altitude > 0.0:
        logging.debug(altitude)
        # 10cm accuracy is enough for altitudes
        return round(altitude, 1)
    else:
        return None


def filter_distance(distance):
    """Returns the distance given in parameter rounded one decimal place"""
    # 10cm accuracy is enough for distances
    return round(distance, 1)


def filter_coordinate(coordinate):
    """Returns the coordinate given in parameter, rounder three decimal places"""
    # 1mm accuracy is enough for coordinates
    return round(coordinate, 3)
