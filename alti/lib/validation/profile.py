# -*- coding: utf-8 -*-

import geojson
from pyramid.httpexceptions import HTTPBadRequest

from shapely.geometry import asShape, Polygon


bboxes = {
    2056: (2450000, 1030000, 2900000, 1350000),
    21781: (450000, 30000, 900000, 350000)
}


class ProfileValidation(object):

    def __init__(self):
        self._linestring = None
        self._layers = None
        self._nb_points = None
        self._ma_offset = None

    def srs_guesser(self):
        sr = None
        if self.linestring is not None:
            for epsg, bbox in bboxes.iteritems():
                dtm_poly = Polygon([
                    (bbox[0], bbox[1]),
                    (bbox[2], bbox[1]),
                    (bbox[2], bbox[3]),
                    (bbox[0], bbox[3])])
                if dtm_poly.contains(self.linestring):
                    sr = epsg
                    break
        return sr

    @property
    def linestring(self):
        return self._linestring

    @property
    def layers(self):
        return self._layers

    @property
    def sr(self):
        return self._sr

    @property
    def nb_points(self):
        return self._nb_points

    @property
    def ma_offset(self):
        return self._ma_offset

    @linestring.setter
    def linestring(self, value):
        if value is None or value == '':
            raise HTTPBadRequest("Missing parameter geom")
        try:
            geom = geojson.loads(value, object_hook=geojson.GeoJSON.to_instance)
        except ValueError:
            raise HTTPBadRequest("Error loading geometry in JSON string")
        try:
            shape = asShape(geom)
        except Exception:
            raise HTTPBadRequest("Error converting JSON to Shape")
        try:
            shape.is_valid
        except Exception:
            raise HTTPBadRequest("Invalid Linestring syntax")

        self._linestring = shape

    @layers.setter
    def layers(self, value):
        if value is None:
            self._layers = ['DTM25']
        else:
            value = value.split(',')
            for i in value:
                if i not in ('DTM25', 'DTM2', 'COMB'):
                    raise HTTPBadRequest("Please provide a valid name for the elevation model DTM25, DTM2 or COMB")
            value.sort()
            self._layers = value

    @sr.setter
    def sr(self, value):
        if value not in (21781, 2056):
            raise HTTPBadRequest("Please provide a valid number for the spatial reference system model 21781 or 2056")
        self._sr = value

    @nb_points.setter
    def nb_points(self, value):
        if value is None:
            self._nb_points = self.nb_points_default
        else:
            if value.isdigit() and int(value) <= self.nb_points_max:
                self._nb_points = int(value)
            else:
                raise HTTPBadRequest("Please provide a numerical value for the parameter 'NbPoints'/'nb_points'" +
                    " smaller than {}".format(self.nb_points_max))

    @ma_offset.setter
    def ma_offset(self, value):
        if value is None:
            self._ma_offset = 3
        else:
            if value.isdigit():
                self._ma_offset = int(value)
            else:
                raise HTTPBadRequest("Please provide a numerical value for the parameter 'offset'")
