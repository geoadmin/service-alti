# -*- coding: utf-8 -*-

import geojson
from pyramid.httpexceptions import HTTPBadRequest

from shapely.geometry import asShape


class ProfileValidation(object):

    def __init__(self):
        self._linestring = None
        self._layers = None
        self._nb_points = None
        self._offset = None
        self._projection = None

    @property
    def linestring(self):
        return self._linestring

    @property
    def layers(self):
        return self._layers

    @property
    def nb_points(self):
        return self._nb_points

    @property
    def projection(self):
        return self._projection

    @property
    def offset(self):
        return self._offset

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
            self._layers = ['COMB']
        else:
            value = value.split(',')
            for i in value:
                if i not in ('DTM25', 'DTM2', 'COMB'):
                    raise HTTPBadRequest("Please provide a valid name for the elevation model DTM25, DTM2 or COMB")
            value.sort()
            self._layers = value

    @nb_points.setter
    def nb_points(self, value):
        print "value is : " + repr(value) + " is int : " + repr(isinstance(value, int))
        if value is None:
            self._nb_points = self.nb_points_default
        elif (isinstance(value, int) or value.isdigit()) and int(value) <= self.nb_points_max:
            self._nb_points = int(value)
        else:
            raise HTTPBadRequest("Please provide a numerical value for the parameter 'NbPoints'/'nb_points'" +
                                 " smaller than {}".format(self.nb_points_max))

    @projection.setter
    def projection(self, value):
        if value not in (21781, 2056):
            raise HTTPBadRequest("Please provide a valid number for the spatial reference system model 21781 or 2056")
        self._projection = value

    @offset.setter
    def offset(self, value):
        if value is None:
            self._offset = 3
        else:
            print value
            if value.isdigit():
                self._offset = int(value)
            else:
                raise HTTPBadRequest("Please provide a numerical value for the parameter 'offset'")
