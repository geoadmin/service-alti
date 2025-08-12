import json
import random

from shapely.geometry import LineString
from shapely.geometry import Point
from shapely.geometry import mapping


def generate_random_coord(srid):
    if srid == 2056:
        minx, miny = 2628750, 1170000
        maxx, maxy = 2637500, 1176000
    else:
        minx, miny = 628750, 170000
        maxx, maxy = 637500, 176000

    yield random.randint(minx, maxx), random.randint(miny, maxy)


def generate_random_point(nb_pts, srid):
    for i in range(nb_pts):
        for x, y in generate_random_coord(srid):
            yield Point(x, y)


def create_json(nb_pts, srid=2056):
    # pylint: disable=unnecessary-comprehension
    random_points = [p for p in generate_random_point(nb_pts, srid)]
    line = LineString(random_points)
    return json.dumps(mapping(line))
