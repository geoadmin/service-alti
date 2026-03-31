import math


# float('NaN') does not raise an Exception. This function does.
def float_raise_nan(val):
    ret = float(val)
    if math.isnan(ret):
        raise ValueError('nan is not considered valid float')
    return ret


def filter_altitude(altitude):
    """Returns the altitude given in parameter, rounded one decimal place"""
    if altitude is not None and altitude > 0.0:
        # 10cm accuracy is enough for altitudes
        return round(float(altitude), 1)
    return None


def filter_distance(distance):
    """Returns the distance given in parameter rounded one decimal place"""
    # 10cm accuracy is enough for distances
    return round(distance, 1)


def filter_coordinate(coordinate):
    """Returns the coordinate given in parameter, rounder three decimal places"""
    # 1mm accuracy is enough for coordinates
    return round(coordinate, 3)


def strtobool(value) -> bool:
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    value = value.lower()
    if value in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    if value in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    raise ValueError(f"invalid truth value \'{value}\'")
