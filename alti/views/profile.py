# -*- coding: utf-8 -*-

import math
from pyramid.view import view_config

from shapely.geometry import LineString

from alti.lib.helpers import filter_altitude, filter_coordinate, filter_distance
from alti.lib.validation.profile import ProfileValidation
from alti.lib.raster.georaster import get_raster
from alti.lib.validation import srs_guesser

from pyramid.httpexceptions import HTTPBadRequest

PROFILE_MAX_AMOUNT_POINTS = 500
PROFILE_DEFAULT_AMOUNT_POINTS = 200


class Profile(ProfileValidation):

    def __init__(self, request):
        super(Profile, self).__init__()
        self.nb_points_max = int(request.registry.settings.get('profile_nb_points_maximum',
                                                               PROFILE_MAX_AMOUNT_POINTS))
        self.nb_points_default = int(request.registry.settings.get('profile_nb_points_default',
                                                                   PROFILE_DEFAULT_AMOUNT_POINTS))

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
            self.layers = 'COMB'

        # number of points wanted in the final profile.
        if 'nbPoints' in request.params:
            self.nb_points = request.params.get('nbPoints')
            self.is_custom_nb_points = True
        elif 'nb_points' in request.params:
            self.nb_points = request.params.get('nb_points')
            self.is_custom_nb_points = True
        else:
            self.nb_points = self.nb_points_default
            self.is_custom_nb_points = False

        # param sr (or projection, sr meaning spatial reference), which Swiss projection to use.
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
            self.projection = sr

        # param offset, used for smoothing. define how many coordinates should be included
        # in the window used for smoothing. If not defined (or value is zero) smoothing is disabled.
        if 'offset' in request.params:
            self.offset = request.params.get('offset')

        # param resolution, how far away each point should be when the line defined in geom is filled up with points
        # by default, will be 2 meter as this is the meshing of the raster model. Any value below 2 meters will be
        # forced to 2 meters.
        if 'resolution' in request.params:
            self.resolution = int(request.params.get('resolution'))
            if self.resolution < 2:
                self.resolution = 2
            self.is_custom_resolution = True
        else:
            self.resolution = 2
            self.is_custom_resolution = False

        # param only_requested_points, which is flag that when set to True will make
        # the profile with only the given points in geom (no filling points)
        if 'only_requested_points' in request.params:
            self.only_requested_points = bool(request.params.get('only_requested_points'))
        else:
            self.only_requested_points = False

        # param distinct_points, which if set true will add the points given in param geom into the profile
        if 'distinct_points' in request.params:
            self.distinct_points = bool(request.params.get('distinct_points'))
        else:
            self.distinct_points = False

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
        rasters = [get_raster(layer, self.projection) for layer in self.layers]

        if self.only_requested_points:
            coordinates = self.linestring.coords
        else:
            # filling lines defined by coordinates (linestring) with as much point as possible (elevation model is
            # a 2m mesh, so no need to go beyond that)
            coordinates = self.__create_points(self.linestring.coords, self.nb_points)

        # extract z values (altitude over distance) for coordinates
        z_values = self.__extract_z_values(rasters, coordinates)

        return self.__create_response(coordinates,
                                      # if offset is defined, do the smoothing
                                      self.__smooth(z_values) if self.offset > 0 else z_values,
                                      output_to_json)

    def __create_response(self, coordinates, z_values, output_to_json):
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

    def __smooth(self, z_values):
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
        return z_values_with_smoothing

    def __create_points(self, coordinates, nb_points):
        """
            Add some points in order to reach the requested number of points. Points will be added as close as possible
            as to not exceed the altitude model meshing (which is 2 meters).
        """

        # if param distinct_points is True, we count how many coordinates we have received in geom and adapt
        # resolution accordingly (to reach nb_points), if set to False we count two extra points (one for the first and
        # one for last point, which will be included anyway)
        nb_extra_points = len(coordinates) if self.distinct_points is True else 2

        # calculate total distance for the entire geom
        total_distance = 0
        previous_coordinate = None
        for coordinate in coordinates:
            if previous_coordinate is not None:
                total_distance += Profile.__distance_between(previous_coordinate, coordinate)
            previous_coordinate = coordinate

        if total_distance <= 0.0 or len(coordinates) >= nb_points:
            return coordinates

        # checking if total distance divided by resolution is an amount of point smaller or equals to
        # number of points requested
        verified_resolution = self.resolution
        if total_distance / self.resolution + nb_extra_points > nb_points:
            # if greater, calculate a new resolution that will match the requested amount of points
            # we return a special http code for this case (see https://github.com/geoadmin/service-alti/issues/43)
            # if the user has provided a custom resolution, or a specific number of points
            # we notify him that we had to change it by returning HTTP 203 as a response
            if self.is_custom_resolution or self.is_custom_nb_points:
                self.request.response.status = 203
            verified_resolution = round(total_distance / (nb_points - nb_extra_points), 3)

        # filling each segment with points spaced by 'verified_resolution'
        # here's a quick recap on how it works
        # geom: p1 - - - - - - - - - p2 - - - - - - - - - - p3
        # result: p1 = p = p = p = p = p - p2 - p = p = p = p = p = p = p - p3
        # where '=' sign means a distance equal to the verified_resolution, the tricky part is the intersection with
        # p2, where we need to place p2 in the middle of a verified_resolution (sum of both '-' around p2 equals
        # verified_distance), if we do not do that, the result will have fewer points as required by the param nb_points
        # whether p2 will be added to the list depends on param 'distinct_points'
        result = []
        previous_coordinate = None
        # used for keeping the resolution going in between points in the middle of a segment (see p2 above)
        leftover_distance = 0
        for coordinate in coordinates:
            if previous_coordinate is not None:
                line = LineString([previous_coordinate, coordinate])
                line_length = round(line.length, 3)
                line_length_covered = 0
                previous_point = None

                while line_length_covered < line_length:
                    # generating next point along the line
                    if leftover_distance > 0:
                        line_length_covered += leftover_distance
                        leftover_distance = 0
                    else:
                        line_length_covered += verified_resolution
                    point_along_line = line.interpolate(line_length_covered)

                    # if this is the last point of the line, we have to remember the distance between the previous
                    # and the last point, so that we can place the first point of the next segment at exactly
                    # the resolution (see explanations above)
                    if previous_point is not None and (line_length_covered + verified_resolution) > line_length:
                        leftover_distance = round(verified_resolution - LineString([previous_point,
                                                                                    point_along_line]).length, 3)
                    previous_point = point_along_line

                    if self.distinct_points is True or leftover_distance == 0:
                        result.append([filter_coordinate(point_along_line.x),
                                       filter_coordinate(point_along_line.y)])

            else:
                # placing the first point of the geom
                result.append([filter_coordinate(coordinate[0]),
                               filter_coordinate(coordinate[1])])

            previous_coordinate = coordinate

        # placing the last point of the geom in case it wasn't added above (when param distinct_points is False)
        if self.distinct_points is False:
            result.append([filter_coordinate(previous_coordinate[0]),
                           filter_coordinate(previous_coordinate[1])])

        # if we couldn't match nb_points because we were asked for too much point for a small distance (only one point
        # is placed every two meters) we return HTTP 203
        if self.is_custom_nb_points and nb_points > len(result):
            self.request.response.status = 203

        return result

    def __extract_z_values(self, rasters, coordinates):
        z_values = {}
        for i in xrange(0, len(self.layers)):
            z_values[self.layers[i]] = []
            for j in xrange(0, len(coordinates)):
                z = rasters[i].getVal(coordinates[j][0], coordinates[j][1])
                z_values[self.layers[i]].append(z)
        return z_values

    @staticmethod
    def __distance_between(coord1, coord2):
        """Compute the distance between 2 points"""
        return filter_distance(math.sqrt(math.pow(coord1[0] - coord2[0], 2.0) + math.pow(coord1[1] - coord2[1], 2.0)))

    @staticmethod
    def __factor(x):
        return float(1) / (abs(x) + 1)
