import math

from pyramid.httpexceptions import HTTPInternalServerError
from shapely.geometry import LineString
from scipy.spatial.distance import pdist, squareform

from alti.lib.raster.georaster import get_raster
from alti.lib.helpers import filter_coordinate, filter_distance, filter_altitude, transform_shape
from alti.lib.validation.profile import PROFILE_DEFAULT_AMOUNT_POINTS


def get_profile(geom=None,
                spatial_reference_in=None,
                spatial_reference_out=None,
                native_srs=None,
                nb_points=PROFILE_DEFAULT_AMOUNT_POINTS,
                offset=0,
                only_requested_points=False,
                smart_filling=False,
                output_to_json=True):
    """Compute the alt=fct(dist) array and store it in c.points"""

    # get raster data from georaster.py
    raster = get_raster(spatial_reference_in)

    if only_requested_points:
        coordinates = geom.coords
    else:
        # filling lines defined by coordinates (linestring) with as much point as possible (elevation model is
        # a 2m mesh, so no need to go beyond that)
        coordinates = _create_points(coordinates=geom.coords,
                                     smart_filling=smart_filling,
                                     nb_points=nb_points)

    # extract z values (altitude over distance) for coordinates
    z_values = _extract_z_values(raster=raster,
                                 coordinates=coordinates)

    return _create_profile(coordinates=coordinates,
                           # if offset is defined, do the smoothing
                           z_values=_smooth(layers, offset, z_values) if offset > 0 else z_values,
                           spatial_reference_in=spatial_reference_in,
                           spatial_reference_out=spatial_reference_out,
                           native_srs=native_srs,
                           output_to_json=output_to_json,
                           # if Web Mercator, rounding at 6th decimal is about 0.11m at equator
                           # for swiss sptial references, 3 digits are enough (0.001m)
                           rounding_digits_for_coordinates=6 if spatial_reference_out == 4326 else 3)


def _create_profile(coordinates,
                    z_values,
                    spatial_reference_in,
                    spatial_reference_out,
                    native_srs,
                    output_to_json,
                    rounding_digits_for_coordinates=3):
    total_distance = 0
    previous_coordinates = None
    if output_to_json:
        profile = []
    else:
        # If the renderer is a csv file
        profile = {'headers': ['Distance'], 'rows': []}
        profile['headers'].append('Easting')
        profile['headers'].append('Northing')

    if spatial_reference_out is not None and spatial_reference_in != spatial_reference_out:
        try:
            geom = LineString(coordinates)
            reprojected_geom = transform_shape(geom, native_srs, spatial_reference_out)
            coordinates = list(reprojected_geom.coords)
        except:
            raise HTTPInternalServerError('Cannot reproject coordinates back to {}'.format(spatial_reference_out))

    for j in xrange(0, len(coordinates)):
        if previous_coordinates is not None:
            total_distance += _distance_between(previous_coordinates, coordinates[j])
        # if the altitude is under 0 meters or is None, filter altitude returns None
        alt = filter_altitude(z_values[j])
        if alt is not None:
            rounded_dist = filter_distance(total_distance)
            if output_to_json:
                profile.append({
                    'alts': alt,
                    'dist': rounded_dist,
                    'easting': filter_coordinate(coordinates[j][0], digits=rounding_digits_for_coordinates),
                    'northing': filter_coordinate(coordinates[j][1], digits=rounding_digits_for_coordinates)
                })
            # For csv file
            else:
                temp = [rounded_dist]
                if alt is not None:
                    temp.append(alt)
                temp.append(filter_coordinate(coordinates[j][0], digits=rounding_digits_for_coordinates))
                temp.append(filter_coordinate(coordinates[j][1], digits=rounding_digits_for_coordinates))
                profile['rows'].append(temp)
        previous_coordinates = coordinates[j]
    return profile


def _smart_fill(coordinates, nb_points):
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


def _dumb_fill(coordinates, nb_points):
    """
        Add some points in order to reach roughly the asked
        number of points.
    """
    total_length = 0
    prev_coord = None
    for coord in coordinates:
        if prev_coord is not None:
            total_length += _distance_between(prev_coord, coord)
        prev_coord = coord

    if total_length == 0.0:
        return coordinates

    result = []
    prev_coord = None
    for coord in coordinates:
        if prev_coord is not None:
            cur_length = _distance_between(prev_coord, coord)
            cur_nb_points = int((nb_points - 1) * cur_length / total_length + 0.5)
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


def _create_points(coordinates, smart_filling, nb_points):
    """
        Add some points in order to reach the requested number of points. If smart_filling is true, points will be added
        as close as possible as to not exceed the altitude model meshing (which is 2 meters). If not, they will be just
        thrown at equal distance without any regards to model resolution.
    """
    if smart_filling:
        return _smart_fill(coordinates, nb_points)
    else:
        return _dumb_fill(coordinates, nb_points)


def _extract_z_values(raster, coordinates):
    # keeping track of tiles that have been used for another coordinates (usually coordinates are close together)
    # this way we increase our chances to find the required tile without looking on the whole country tiles
    tiles = []
    z_values = []
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
            tile = raster.get_tile(x, y)
            tiles.append(tile)
            z = tile.get_height_for_coordinate(x, y)
        z_values.append(z)
    # at the end we close all tile files
    for tile in tiles:
        tile.close_file()
    return z_values


def _smooth(offset, z_values):
    z_values_with_smoothing = []
    for j in xrange(0, len(z_values)):
        s = 0
        d = 0
        if z_values[j] is None:
            z_values_with_smoothing.append(None)
            continue
        for k in xrange(-offset, offset + 1):
            p = j + k
            if p < 0 or p >= len(z_values):
                continue
            if z_values[p] is None:
                continue
            s += z_values[p] * _factor(k)
            d += _factor(k)
        z_values_with_smoothing.append(s / d)
    return z_values_with_smoothing


def _distance_between(coord1, coord2):
    """Compute the distance between 2 points"""
    return filter_distance(math.sqrt(math.pow(coord1[0] - coord2[0], 2.0) + math.pow(coord1[1] - coord2[1], 2.0)))


def _factor(x):
    return float(1) / (abs(x) + 1)
