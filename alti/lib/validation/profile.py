# -*- coding: utf-8 -*-

import geojson
from pyramid.httpexceptions import HTTPBadRequest

from shapely.geometry import shape
from alti.lib.validation import SrsValidation

PROFILE_MAX_AMOUNT_POINTS = 5000
PROFILE_DEFAULT_AMOUNT_POINTS = 200


class ProfileValidation(SrsValidation):

    def __init__(self):
        self._linestring = None
        self._nb_points = None
        self._offset = None
        self._spatial_reference = None
        self.nb_points_default = None
        self.nb_points_max = None

    @property
    def linestring(self):
        return self._linestring

    @property
    def spatial_reference(self):
        return self._spatial_reference

    @property
    def nb_points(self):
        return self._nb_points

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
            geomToShape = shape(geom)
        except Exception:
            raise HTTPBadRequest("Error converting JSON to Shape")
        try:
            geomToShape.is_valid
        except Exception:
            raise HTTPBadRequest("Invalid Linestring syntax")

        self._linestring = geomToShape

    @spatial_reference.setter
    def spatial_reference(self, value):
        if value not in (21781, 2056):
            raise HTTPBadRequest("Please provide a valid number for the spatial reference system model (on of {})"
                                 .format(self.supported_srs))
        self._spatial_reference = value

    @nb_points.setter
    def nb_points(self, value):
        if value is None:
            self._nb_points = PROFILE_DEFAULT_AMOUNT_POINTS
        elif (isinstance(value, int) or value.isdigit()) and int(value) <= 1:
            raise HTTPBadRequest("Please provide a numerical value for the parameter 'NbPoints'/'nb_points' greater "
                                 "or equal to 2")
        elif (isinstance(value, int) or value.isdigit()) and int(value) <= PROFILE_MAX_AMOUNT_POINTS:
            self._nb_points = int(value)
        else:
            raise HTTPBadRequest("Please provide a numerical value for the parameter 'NbPoints'/'nb_points'" +
                                 " smaller than {}".format(PROFILE_MAX_AMOUNT_POINTS))

    @offset.setter
    def offset(self, value):
        if value is None:
            self._offset = 3
        else:
            if value.isdigit():
                self._offset = int(value)
            else:
                raise HTTPBadRequest("Please provide a numerical value for the parameter 'offset'")
