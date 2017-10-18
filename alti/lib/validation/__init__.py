# -*- coding: utf-8 -*-


from shapely.geometry import Polygon


bboxes = {
    2056: (2450000, 1030000, 2900000, 1350000),
    21781: (450000, 30000, 900000, 350000)
}


def srs_guesser(geom):
    sr = None
    try:
        geom_type = geom.geom_type
    except ValueError:
        return sr

    if geom_type in ('Point', 'LineString'):
        for epsg, bbox in bboxes.iteritems():
            dtm_poly = Polygon([(bbox[0], bbox[1]), (bbox[2], bbox[1]), (bbox[2], bbox[3]), (bbox[0], bbox[3])])
            if dtm_poly.contains(geom):
                sr = epsg
                break
    return sr
