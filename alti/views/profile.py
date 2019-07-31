# -*- coding: utf-8 -*-

import math
from pyramid.view import view_config

from alti.lib.helpers import filter_altitude, filter_coordinate, filter_distance
from alti.lib.validation.profile import ProfileValidation
from alti.lib.raster.georaster import get_raster
from alti.lib.validation import srs_guesser

from pyramid.httpexceptions import HTTPBadRequest


class Profile(ProfileValidation):

    def __init__(self, request):
        super(Profile, self).__init__()
        self.nb_points_default = int(request.registry.settings.get('profile_nb_points_default', 200))
        self.nb_points_max = int(request.registry.settings.get('profile_nb_points_maximum', 500))

        # param geom, list of coordinates defining the line on which we want a profile
        if 'geom' in request.params:
            self.linestring = request.params.get('geom')
        else:
            self.linestring = request.body
        if not self.linestring:
            raise HTTPBadRequest("No 'geom' given, cannot create a profile without coordinates")

        # param layers (or elevations_models), define on which elevation model the profile has to be made.
        # Possible values are DTM25, DTM2 and COMB (have a look at georaster.py for more info on this)
        # default value is COMB
        if 'layers' in request.params:
            self.layers = request.params.get('layers')
        elif 'elevation_models' in request.params:
            self.layers = request.params.get('elevation_models')
        else:
            self.layers = ['COMB']

        # param nbPoints (or nb_points), define how much point we want to have in the profile output
        # if not defined, a calculation will be made in order to have as many points as possible, taking into account
        # the resolution param bellow (max number of points is a hard limit, so if filling the coords every 'resolution'
        # leads to to much points, 'resolution' will be increased to accommodate and not overcome the hard limitation
        # on how much point is possible in a profile)
        if 'nbPoints' in request.params:
            self.nb_points = request.params.get('nbPoints')
        elif 'nb_points' in request.params:
            self.nb_points = request.params.get('nb_points')

        # param sr (or projection, sr meaning "système de référence"), which Swiss projection to use.
        # Possible values are expressed in int, so value for EPSG:2056 (LV95) is 2056
        # and value for EPSG:21781 (LV03) is 21781
        # if this param is not present, it will be guessed from the coordinates present in the param geom
        if 'sr' in request.params:
            self.projection = int(request.params.get('sr'))
        elif 'projection' in request.params:
            self.projection = int(request.params.get('projection'))
        else:
            sr = srs_guesser(self.linestring)
            if sr is None:
                raise HTTPBadRequest("No 'sr' given and cannot be guessed from 'geom'")
            self.sr = sr

        # param offset, used for smoothing. define how many coordinates should be included
        # in the window used for smoothing. If not defined (or value is zero) smoothing is disabled.
        if 'offset' in request.params:
            self.offset = int(request.params.get('offset'))
        else:
            self.offset = 0

        # param resolution, how far away each point should be when the line defined in geom is filled up with points
        # by default, will be 2 meter as this is the meshing of the raster model. Any value below 2 meters will be
        # forced to 2 meters.
        if 'resolution' in request.params:
            self.resolution = int(request.params.get('resolution'))
            if self.resolution < 2:
                self.resolution = 2
        else:
            self.resolution = 2

        # keeping the request for later use
        self.request = request

    @view_config(route_name='profile_json', renderer='jsonp', http_cache=0)
    def json(self):
        return self.__compute_points(True)

    @view_config(route_name='profile_csv', renderer='csv', http_cache=0)
    def csv(self):
        return self.__compute_points(False)

    def __compute_points(self, output_to_json):
        """Compute the alt=fct(dist) array and store it in c.points"""

        # get raster data from georaster.py (layers is sometime referred as elevation_models in request parameters)
        rasters = [get_raster(layer, self.sr) for layer in self.layers]

        # filling lines defined by coordinates (linestring) with as much point as possible (elevation model is
        # a 2m mesh, so no need to go beyond that)
        coordinates = Profile.__create_points(self.linestring.coords, self.nb_points, self.resolution)

        # extract z values (altitude over distance) for coordinates
        z_values = {}
        for i in xrange(0, len(self.layers)):
            z_values[self.layers[i]] = []
            for j in xrange(0, len(coordinates)):
                z = rasters[i].getVal(coordinates[j][0], coordinates[j][1])
                z_values[self.layers[i]].append(z)

        # if offset is defined, do the smoothing
        if self.offset > 0:
            z_values_with_smoothing = {}
            for i in xrange(0, len(self.layers)):
                z_values_with_smoothing[self.layers[i]] = []
                for j in xrange(0, len(z_values[self.layers[i]])):
                    s = 0
                    d = 0
                    if z_values[self.layers[i]][j] is None:
                        z_values_with_smoothing[self.layers[i]].append(None)
                        continue
                    for k in xrange(-self.offset, self.offset + 1):
                        p = j + k
                        if p < 0 or p >= len(z_values[self.layers[i]]):
                            continue
                        if z_values[self.layers[i]][p] is None:
                            continue
                        s += z_values[self.layers[i]][p] * Profile.__factor(k)
                        d += Profile.__factor(k)
                    z_values_with_smoothing[self.layers[i]].append(s / d)
            # overriding zValues when smoothing has been done
            z_values = z_values_with_smoothing

        total_distance = 0
        previous_coordinates = None
        if output_to_json:
            profile = []
        else:
            # If the renderer is a csv file
            profile = {'headers': ['Distance'], 'rows': []}
            for layer in self.layers:
                profile['headers'].append(layer)
            profile['headers'].append('Easting')
            profile['headers'].append('Northing')

        for j in xrange(0, len(coordinates)):
            if previous_coordinates is not None:
                total_distance += Profile.__distance_between(previous_coordinates, coordinates[j])
            alts = {}
            for i in xrange(0, len(self.layers)):
                if z_values[self.layers[i]][j] is not None:
                    alts[self.layers[i]] = filter_altitude(
                        z_values[self.layers[i]][j])
            if len(alts) > 0:
                rounded_dist = filter_distance(total_distance)
                if output_to_json:
                    profile.append({
                        'alts': alts,
                        'dist': rounded_dist,
                        'easting': filter_coordinate(coordinates[j][0]),
                        'northing': filter_coordinate(coordinates[j][1])
                    })
                # For csv file
                else:
                    temp = [rounded_dist]
                    for i in alts.iteritems():
                        temp.append(i[1])
                    temp.append(filter_coordinate(coordinates[j][0]))
                    temp.append(filter_coordinate(coordinates[j][1]))
                    profile['rows'].append(temp)
            previous_coordinates = coordinates[j]
        return profile

    @staticmethod
    def __distance_between(coord1, coord2):
        """Compute the distance between 2 points"""
        return math.sqrt(math.pow(coord1[0] - coord2[0], 2.0) +
                         math.pow(coord1[1] - coord2[1], 2.0))

    @staticmethod
    def __create_points(coords, nb_points, resolution):
        """
            Add some points in order to reach roughly the asked
            number of points.
        """

        if nb_points is None or nb_points is 0:
            return coords

        total_length = 0
        prev_coord = None
        for coord in coords:
            if prev_coord is not None:
                total_length += Profile.__distance_between(prev_coord, coord)
            prev_coord = coord

        if total_length == 0.0:
            return coords

        result = []
        prev_coord = None
        for coord in coords:
            if prev_coord is not None:
                cur_length = Profile.__distance_between(prev_coord, coord)
                cur_nb_points = int(nb_points * cur_length / total_length + 0.5)
                if cur_nb_points < 1:
                    cur_nb_points = 1
                dx = (coord[0] - prev_coord[0]) / float(cur_nb_points)
                dy = (coord[1] - prev_coord[1]) / float(cur_nb_points)
                for i in xrange(1, cur_nb_points + 1):
                    result.append(
                        [prev_coord[0] + dx * i,
                         prev_coord[1] + dy * i])
            else:
                result.append([coord[0], coord[1]])
            prev_coord = coord
        return result

    @staticmethod
    def __factor(x):
        return float(1) / (abs(x) + 1)
