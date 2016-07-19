# -*- coding: utf-8 -*-

import math


# float('NaN') does not raise an Exception. This function does.
def float_raise_nan(val):
    ret = float(val)
    if math.isnan(ret):
        raise ValueError('nan is not considered valid float')
    return ret


def filter_alt(alt):
    if alt is not None and alt > 0.0:
        # 10cm accuracy is enough for altitudes
        return round(alt, 1)
