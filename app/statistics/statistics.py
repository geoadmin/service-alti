import json

DATA_FOLDER = "/var/local/geodata/bund/swisstopo/swissalti3d/hikingtime_analysis/"


def load_json(filename):
    with open(DATA_FOLDER + filename, "r", encoding='utf-8') as json_file:
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
        # all wanderweg paths are expressed as LineString wrapped into a FeatureCollection (FME
        # exports this way so that metadata can be added with it). Here we unwrap the geometry and
        # export it alone (to be directly fed into profile service in the future)
        linestring_geojson = feature_collection_geojson['features'][0]['geometry']
        official_time = wanderweg['officialStZie'] if 'officialStZie' in wanderweg else 0
        elevation_up = wanderweg['HoeheAufE'] if 'HoeheAufE' in wanderweg else 0
        elevation_down = wanderweg['HoeheAbE'] if 'HoeheAbE' in wanderweg else 0
        elevation_min = wanderweg['HoeheMinE'] if 'HoeheMinE' in wanderweg else 0
        elevation_max = wanderweg['HoeheMaxE'] if 'HoeheMaxE' in wanderweg else 0
        total_distance = wanderweg['LaengeE'] if 'LaengeE' in wanderweg else 0
        official_time_reversed = wanderweg['officialZieSt'] if 'officialZieSt' in wanderweg else 0
        geoadmin_time_pre_overhaul = wanderweg['ZeitStZiE'] if 'ZeitStZiE' in wanderweg else 0
        geoadmin_time_reversed_pre_overhaul = wanderweg['ZeitZiStE'
                                                       ] if 'ZeitZiStE' in wanderweg else 0
        data.append(
            {
                'id': wanderweg['OBJECTID'],
                'name': wanderweg['NameE'],
                'officialTime':
                    {
                        'startToFinish': official_time,
                        'finishToStart': official_time_reversed,
                        'elevationUp': elevation_up,
                        'elevationDown': elevation_down,
                        'elevationMax': elevation_max,
                        'elevationMin': elevation_min,
                        'totalDistance': total_distance,
                    },
                'geoadminBefore':
                    {
                        'startToFinish': geoadmin_time_pre_overhaul,
                        'finishToStart': geoadmin_time_reversed_pre_overhaul
                    },
                'wanderweg_length': wanderweg['SHAPE_Leng'],
                'geojson': linestring_geojson,
            }
        )
    return json.dumps(data)
