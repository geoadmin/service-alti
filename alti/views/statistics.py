import json

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.renderers import render_to_response

import logging
log = logging.getLogger('alti')

DATA_FOLDER = "/var/local/geodata/bund/swisstopo/swissalti3d/hikingtime_analysis/"


def load_json(filename):
    json_file = open(DATA_FOLDER + filename, "r")
    if json_file is None:
        raise IOError("No metadata file found")
    json_data = json.load(json_file)
    if json_data is None:
        return IOError("Failed to load JSON")
    return json_data


def prepare_data(metadata):
    data = []
    for wanderweg in metadata:
        feature_collection_geojson = load_json(wanderweg['geojson_file'] + '.lv95.json')
        # all wanderweg paths are expressed as LineString wrapped into a FeatureCollection (FME exports this way
        # so that metadata can be added with it). Here we unwrap the geometry and export it alone (to be directly
        # fed into profile service in the future)
        linestring_geojson = feature_collection_geojson['features'][0]['geometry']
        official_time = wanderweg['officialStZie'] if 'officialStZie' in wanderweg else 0
        official_time_reversed = wanderweg['officialZieSt'] if 'officialZieSt' in wanderweg else 0
        geoadmin_time_pre_overhaul = wanderweg['ZeitStZiE'] if 'ZeitStZiE' in wanderweg else 0
        geoadmin_time_reversed_pre_overhaul = wanderweg['ZeitZiStE'] if 'ZeitZiStE' in wanderweg else 0
        data.append({
            'id': wanderweg['OBJECTID'],
            'name': wanderweg['NameE'],
            'officialTime': {
                'startToFinish': official_time,
                'finishToStart': official_time_reversed,
            },
            'timePreOverhaul': {
                'startToFinish': geoadmin_time_pre_overhaul,
                'finishToStart': geoadmin_time_reversed_pre_overhaul
            },
            'wanderweg_length': wanderweg['SHAPE_Leng'],
            'geojson': linestring_geojson
        })
    return json.dumps(data)


class StatisticsView(object):

    def __init__(self, request):
        self.request = request

    @view_config(route_name='stats')
    def generate_stats(self):
        return render_to_response('templates/statistics.html.mako',
                                  value={},
                                  request=self.request)

    @view_config(route_name='stats_data')
    def stats_data(self):
        try:
            metadata = load_json("metadata.json")
            return Response(body=prepare_data(metadata), status=200)
        except Exception as e:
            log.error('Error while loading statistic data (Exception: %s)' % e)
            return Response(body=e.message, status=400)
