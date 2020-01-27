# -*- coding: utf-8 -*-


from shapely.geometry import box


extents = {
    2056: (2450000, 1030000, 2900000, 1350000),
    21781: (450000, 30000, 900000, 350000),
    3857: (603111.3901608731, 5677741.733673414, 1277662.4228336029, 6154011.090045582),
    4326: (5.41784179808085, 45.35600083019525, 11.477436823766046, 48.28267323232726)

}


def init_bboxes():
    bboxes = {}
    for epsg, bbox in extents.iteritems():
        dtm_poly = box(*bbox)
        bboxes[epsg] = dtm_poly
    return bboxes

bboxes = init_bboxes()


class SrsValidation(object):

    def srs_guesser(self, geom):
        sr = None
        try:
            geom_type = geom.geom_type
        except ValueError:
            return sr

        if geom_type in ('Point', 'LineString'):
            for epsg, bbox in bboxes.iteritems():
                if bbox.contains(geom):
                    sr = epsg
                    break
        return sr
