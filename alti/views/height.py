# -*- coding: utf-8 -*-

from shapely.geometry import Point
from alti.lib.validation import srs_guesser, bboxes
from alti.lib.validation.height import HeightValidation
from alti.lib.height_helpers import get_height

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest


class Height(HeightValidation):

    def __init__(self, request):
        super(Height, self).__init__()
        if 'easting' in request.params:
            self.lon = request.params.get('easting')
        else:
            self.lon = request.params.get('lon')
        if 'northing' in request.params:
            self.lat = request.params.get('northing')
        else:
            self.lat = request.params.get('lat')
        if 'sr' in request.params:
            self.sr = int(request.params.get('sr'))
        else:
            point = Point(self.lon, self.lat)
            sr = srs_guesser(point)
            if sr is None:
                raise HTTPBadRequest("No 'sr' given and cannot be guessed from 'geom'")
            else:
                self.sr = sr
        if self.lon < bboxes[self.sr][0] or self.lon > bboxes[self.sr][2] or \
                self.lat < bboxes[self.sr][1] or self.lat > bboxes[self.sr][3]:
            raise HTTPBadRequest("Query is out of bounds")
        self.request = request

    @view_config(route_name='height', renderer='jsonp', http_cache=0)
    def height(self):
        alt = get_height(self.sr, self.lon, self.lat)
        if alt is None:
            raise HTTPBadRequest('Requested coordinate ({},{}) out of bounds in sr {}'.format(self.lon, self.lat, self.sr))

        return {'height': str(alt)}
