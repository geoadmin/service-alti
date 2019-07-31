# -*- coding: utf-8 -*-

import geojson
import json
from shapely import wkt
from shapely.geometry import LineString, MultiLineString, shape, mapping, MultiPoint, Point
from shapely.ops import split, linemerge

# Ouvrir le geojson et le transformer en shapely

with open('test2.geojson')as test:
  data = test.read()
#  print(data)
  d = json.loads(data)
  features = d['features']
  shapes = [shape(feature['geometry']) for feature in features]
  for s in shapes:
    print(s.length)
    print (s.bounds)
    print(s.coords)
    print(len(s.coords))
    print (s)

print
print

# Découper la ligne en plusieurs segments (pour garder les points donnés par l'utilisateur)

points = MultiPoint(s.coords)

pt = points
line = s
lines = split(line,pt)

# Densifier chaque segment - Découper la ligne à une certaine distance

for line in lines:
    distance = 0.25
    curr_dist = distance
    line = MultiLineString([line])
    line_length = line.length
    list_point = []
    list_point.append(Point(list(line[0].coords)[0]))

    while curr_dist < line_length:
        list_point.append(line.interpolate(curr_dist))
        curr_dist += distance

    list_point.append(Point(list(line[0].coords)[-1]))
    profile = LineString(list_point)
    print(profile)
    print(len(profile.coords))
print ('jusque ici ok')

# Regrouper tous les segments en une ligne




