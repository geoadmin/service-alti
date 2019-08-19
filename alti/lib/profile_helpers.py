import math

from shapely.geometry import LineString

from alti.lib.raster.georaster import get_raster
from alti.lib.helpers import filter_coordinate, filter_distance, filter_altitude


PROFILE_MAX_AMOUNT_POINTS = 500
PROFILE_DEFAULT_AMOUNT_POINTS = 200


def get_profile(geom=None,
                projection=None,
                layers=None,
                nb_points=PROFILE_DEFAULT_AMOUNT_POINTS,
                offset=0,
                resolution=2,
                distinct_points=False,
                only_requested_points=False,
                output_to_json=True):
    """Compute the alt=fct(dist) array and store it in c.points"""

    # get raster data from georaster.py (layers is sometime referred as elevation_models in request parameters)
    if layers is None:
        layers = []
    rasters = [get_raster(layer, projection) for layer in layers]

    if only_requested_points:
        coordinates = geom.coords
    else:
        # filling lines defined by coordinates (linestring) with as much point as possible (elevation model is
        # a 2m mesh, so no need to go beyond that)
        coordinates = __create_points(coordinates=geom.coords,
                                      nb_points=nb_points,
                                      resolution=resolution,
                                      distinct_points=distinct_points)

    # extract z values (altitude over distance) for coordinates
    z_values = __extract_z_values(layers, rasters, coordinates)

    return __create_profile(layers=layers,
                            coordinates=coordinates,
                            # if offset is defined, do the smoothing
                            z_values=__smooth(layers, offset, z_values) if offset > 0 else z_values,
                            output_to_json=output_to_json)


def is_resolution_possible_with_nb_points(coordinates, nb_points, resolution, distinct_points=False):
    verified_resolution = __compute_resolution(coordinates=coordinates,
                                               nb_points=nb_points,
                                               resolution=resolution,
                                               distinct_points=distinct_points)
    return verified_resolution == resolution


def __create_profile(layers, coordinates, z_values, output_to_json):
    total_distance = 0
    previous_coordinates = None
    if output_to_json:
        profile = []
    else:
        # If the renderer is a csv file
        profile = {'headers': ['Distance'], 'rows': []}
        for layer in layers:
            profile['headers'].append(layer)
        profile['headers'].append('Easting')
        profile['headers'].append('Northing')

    for j in xrange(0, len(coordinates)):
        if previous_coordinates is not None:
            total_distance += __distance_between(previous_coordinates, coordinates[j])
        alts = {}
        for i in xrange(0, len(layers)):
            if z_values[layers[i]][j] is not None:
                alts[layers[i]] = filter_altitude(
                    z_values[layers[i]][j])
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


def __compute_resolution(coordinates, nb_points, resolution, distinct_points=False):

    # if param distinct_points is True, we count how many coordinates we have received in geom and adapt
    # resolution accordingly (to reach nb_points), if set to False we count two extra points (one for the first and
    # one for last point, which will be included anyway)
    nb_extra_points = len(coordinates) if distinct_points is True else 2

    # calculate total distance for the entire geom
    total_distance = 0
    previous_coordinate = None
    for coordinate in coordinates:
        if previous_coordinate is not None:
            total_distance += __distance_between(previous_coordinate, coordinate)
        previous_coordinate = coordinate

    # checking if total distance divided by resolution is an amount of point smaller or equals to
    # number of points requested
    if total_distance / resolution + nb_extra_points > nb_points:
        # if greater, calculate a new resolution that will match the requested amount of points
        # we return a special http code for this case (see https://github.com/geoadmin/service-alti/issues/43)
        # if the user has provided a custom resolution, or a specific number of points
        # we notify him that we had to change it by returning HTTP 203 as a response
        return round(total_distance / (nb_points - nb_extra_points), 3)
    else:
        return round(resolution, 3)


def __create_points(coordinates, nb_points, resolution, distinct_points):
    """
        Add some points in order to reach the requested number of points. Points will be added as close as possible
        as to not exceed the altitude model meshing (which is 2 meters).
    """

    if len(coordinates) >= nb_points:
        return coordinates

    # checking if total distance divided by resolution is an amount of point smaller or equals to
    # number of points requested
    verified_resolution = __compute_resolution(coordinates=coordinates,
                                               nb_points=nb_points,
                                               resolution=resolution,
                                               distinct_points=distinct_points)

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

                if distinct_points is True or leftover_distance == 0:
                    result.append([filter_coordinate(point_along_line.x),
                                   filter_coordinate(point_along_line.y)])

        else:
            # placing the first point of the geom
            result.append([filter_coordinate(coordinate[0]),
                           filter_coordinate(coordinate[1])])

        previous_coordinate = coordinate

    # placing the last point of the geom in case it wasn't added above (when param distinct_points is False)
    if distinct_points is False:
        result.append([filter_coordinate(previous_coordinate[0]),
                       filter_coordinate(previous_coordinate[1])])

    return result


def __extract_z_values(layers, rasters, coordinates):
    z_values = {}
    for i in xrange(0, len(layers)):
        z_values[layers[i]] = []
        for j in xrange(0, len(coordinates)):
            z = rasters[i].getVal(coordinates[j][0], coordinates[j][1])
            z_values[layers[i]].append(z)
    return z_values


def __smooth(layers, offset, z_values):
    z_values_with_smoothing = {}
    for i in xrange(0, len(layers)):
        z_values_with_smoothing[layers[i]] = []
        for j in xrange(0, len(z_values[layers[i]])):
            s = 0
            d = 0
            if z_values[layers[i]][j] is None:
                z_values_with_smoothing[layers[i]].append(None)
                continue
            for k in xrange(-offset, offset + 1):
                p = j + k
                if p < 0 or p >= len(z_values[layers[i]]):
                    continue
                if z_values[layers[i]][p] is None:
                    continue
                s += z_values[layers[i]][p] * __factor(k)
                d += __factor(k)
            z_values_with_smoothing[layers[i]].append(s / d)
    return z_values_with_smoothing


def __distance_between(coord1, coord2):
    """Compute the distance between 2 points"""
    return filter_distance(math.sqrt(math.pow(coord1[0] - coord2[0], 2.0) + math.pow(coord1[1] - coord2[1], 2.0)))


def __factor(x):
    return float(1) / (abs(x) + 1)
