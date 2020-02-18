# -*- coding: utf-8 -*-

from pyramid.httpexceptions import HTTPBadRequest

from alti.lib.helpers import float_raise_nan
from alti.lib.validation import SrsValidation


class HeightValidation(SrsValidation):

    def __init__(self):
        self._lon = None
        self._lat = None
        self._sr = None

    @property
    def lon(self):
        return self._lon

    @property
    def lat(self):
        return self._lat

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

    @sr.setter
    def sr(self, value):
        if value not in self.supported_srs:
            raise HTTPBadRequest("Please provide a valid number for the spatial reference system model ({})".format(self.supported_srs))
        self._sr = value
