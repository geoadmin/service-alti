import math

from shapely.geometry import LineString
from scipy.spatial.distance import pdist, squareform

from alti.lib.raster.georaster import get_raster
from alti.lib.helpers import filter_coordinate, filter_distance, filter_altitude


PROFILE_MAX_AMOUNT_POINTS = 10000
PROFILE_DEFAULT_AMOUNT_POINTS = 2000


def get_profile(geom=None,
                projection=None,
                layers=None,
                nb_points=PROFILE_DEFAULT_AMOUNT_POINTS,
                offset=0,
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
                                      nb_points=nb_points)

    # extract z values (altitude over distance) for coordinates
    z_values = __extract_z_values(layers=layers,
                                  rasters=rasters,
                                  coordinates=coordinates)

    return __create_profile(layers=layers,
                            coordinates=coordinates,
                            # if offset is defined, do the smoothing
                            z_values=__smooth(layers, offset, z_values) if offset > 0 else z_values,
                            output_to_json=output_to_json)


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
                alts[layers[i]] = filter_altitude(z_values[layers[i]][j])
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


def __create_points(coordinates, nb_points):
    """
        Add some points in order to reach the requested number of points. Points will be added as close as possible
        as to not exceed the altitude model meshing (which is 2 meters).
    """

    if len(coordinates) >= nb_points:
        return coordinates

    # calculating distances between each points, and total distance
    distances_squareform = squareform(pdist(coordinates))
    amount_distances = len(distances_squareform)
    distances = [0] * (amount_distances - 1)
    for i in range(0, amount_distances - 1):
        distances[i] = distances_squareform[i][i + 1]
    total_distance = sum(distances)
    # total_distance will be used as a divisor later, we have to check it's not zero
    if total_distance == 0:
        return coordinates

    result = []
    previous_coordinate = None
    # for each segment, we will add points in between on a prorata basis (longer segments will have more points)
    for i in range(0, len(coordinates)):
        if previous_coordinate is not None:
            result.append(previous_coordinate)
            # preparing segment properties before placing points
            segment_length = distances[i - 1]
            # if segment length is smaller than tiles resolution (2m) we don't add extra points
            if segment_length > 2:
                segment = LineString([previous_coordinate, coordinates[i]])
                # here is the prorata ratio : if a segment makes X% of the total length, X% of total points will
                # be added to this segment
                ratio_distance = segment_length / total_distance
                # rounding number of points down to the closest integer (casting to int will ignore anything after coma)
                nb_points_for_this_segment = int(nb_points * ratio_distance)
                # little protection against division by zero
                if nb_points_for_this_segment > 0:
                    segment_resolution = segment_length / nb_points_for_this_segment
                    # if segment resolution is smaller than 2m, we force the resolution as it's wasteful to go below
                    if segment_resolution < 2:
                        segment_resolution = 2
                    segment_length_covered = 0
                    nb_points_placed = 0
                    while not nb_points_placed == nb_points_for_this_segment \
                            and segment_length_covered < segment_length:
                        nb_points_placed += 1
                        segment_length_covered += segment_resolution
                        new_point = segment.interpolate(nb_points_placed * segment_resolution)
                        result.append([new_point.x, new_point.y])
        previous_coordinate = coordinates[i]

    return result


def __extract_z_values(layers, rasters, coordinates):
    z_values = {}
    # keeping track of tiles that have been used for another coordinates (usually coordinates are close together)
    # this way we increase our chances to find the required tile without looking on the whole country tiles
    tiles = []
    for i in xrange(0, len(layers)):
        z_values[layers[i]] = []
        for j in xrange(0, len(coordinates)):
            x = coordinates[j][0]
            y = coordinates[j][1]
            z = None
            # looking into already used tile if this point is not included
            for already_used_tile in tiles:
                if already_used_tile.contains(x, y):
                    z = already_used_tile.get_height_for_coordinate(x, y)
                    break
            if z is None:
                tile = rasters[i].get_tile(x, y)
                tiles.append(tile)
                z = tile.get_height_for_coordinate(x, y)
            z_values[layers[i]].append(z)
    # at the end we close all tile files
    for tile in tiles:
        tile.close_file()
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
