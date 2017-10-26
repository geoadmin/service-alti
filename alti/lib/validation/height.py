# -*- coding: utf-8 -*-

from pyramid.httpexceptions import HTTPBadRequest

from alti.lib.helpers import float_raise_nan


class HeightValidation(object):

    def __init__(self):
        self._lon = None
        self._lat = None
        self._layers = None
        self._sr = None

    @property
    def lon(self):
        return self._lon

    @property
    def lat(self):
        return self._lat

    @property
    def layers(self):
        return self._layers

    @property
    def sr(self):
        return self._sr

    @lon.setter
    def lon(self, value):
        if value is None:
            raise HTTPBadRequest("Missing parameter 'easting'/'lon'")
        try:
            self._lon = float_raise_nan(value)
        except ValueError:
            raise HTTPBadRequest("Please provide numerical values for the parameter 'easting'/'lon'")

    @lat.setter
    def lat(self, value):
        if value is None:
            raise HTTPBadRequest("Missing parameter 'northing'/'lat'")
        try:
            self._lat = float_raise_nan(value)
        except ValueError:
            raise HTTPBadRequest("Please provide numerical values for the parameter 'northing'/'lat'")

    @layers.setter
    def layers(self, value):
        if not isinstance(value, list):
            value = value.split(',')
            for i in value:
                if i not in ('DTM25', 'DTM2', 'COMB'):
                    raise HTTPBadRequest("Please provide a valid name for the elevation model DTM25, DTM2 or COMB")
        self._layers = value

    @sr.setter
    def sr(self, value):
        if value not in (21781, 2056):
            raise HTTPBadRequest("Please provide a valid number for the spatial reference system model 21781 or 2056")
        self._sr = value
