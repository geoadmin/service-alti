# -*- coding: utf-8 -*-

from shapely.geometry import Point
from alti import NATIVE_SRS
from alti.lib.helpers import filter_altitude, transform_coordinate
from alti.lib.validation.height import HeightValidation
from alti.lib.raster.georaster import get_raster

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest


class Height(HeightValidation):

    def __init__(self, request):
        super(Height, self).__init__()
        self.native_srs = int(request.registry.settings.get('native_srs', 2056))
        supported_srs = request.registry.settings.get('supported_srs', '2056,21781')
        self.supported_srs = map(int, supported_srs.split(','))

        if 'easting' in request.params:
            self.lon = request.params.get('easting')
        else:
            self.lon = request.params.get('lon')
        if 'northing' in request.params:
            self.lat = request.params.get('northing')
        else:
            self.lat = request.params.get('lat')
        if 'layers' in request.params:
            self.layers = request.params.get('layers')
        elif 'elevation_model' in request.params:
            self.layers = request.params.get('elevation_model')
        else:
            self.layers = ['DTM25']
        if 'sr' in request.params:
            self.sr = int(request.params.get('sr'))
        else:
            point = Point(self.lon, self.lat)
            sr = self.srs_guesser(point)
            if sr is None:
                raise HTTPBadRequest("No 'sr' given and cannot be guessed from 'geom'")
            else:
                self.sr = sr
        if self.sr not in (2056, 21781):
            self.lon, self.lat = transform_coordinate((self.lon, self.lat), self.sr, NATIVE_SRS)
            self.sr_in = NATIVE_SRS
        else:
            self.sr_in = self.sr

        self.request = request

    @view_config(route_name='height', renderer='jsonp', http_cache=0)
    def height(self):
        rasters = [get_raster(layer, self.sr_in) for layer in self.layers]
        alt = filter_altitude(rasters[0].get_height_for_coordinate(self.lon, self.lat))
        if alt is None:
            raise HTTPBadRequest('Requested coordinate ({},{}) out of bounds in sr {}'.format(self.lon, self.lat, self.sr))

        return {'height': str(alt)}
