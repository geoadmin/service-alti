import logging

from flask import abort, render_template, jsonify, make_response, request

from werkzeug.exceptions import HTTPException

from shapely.geometry import Point

from app import app, georaster_utils
from app.helpers import make_error_msg
from app.helpers.route import prefix_route
from app.helpers.height_helpers import get_height
from app.helpers.profile_helpers import get_profile

from app.helpers.validation import srs_guesser, bboxes
from app.helpers.validation.height import validate_lon_lat, validate_sr
import app.helpers.validation.profile as profile_arg_validation

# add route prefix
from app.statistics.statistics import load_json, prepare_data

app.route = prefix_route(app.route, '/rest/services/')

logger = logging.getLogger(__name__)


@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e
    logger.error(str(e))
    return make_error_msg(500, "Internal server error, please consult logs")


@app.route('/checker', methods=['GET'])
def check():
    return make_response(jsonify({'success': True, 'message': 'OK'}))


@app.route('/height')
def height_route():
    if 'easting' in request.args:
        lon = request.args.get('easting')
    else:
        lon = request.args.get('lon')
    if 'northing' in request.args:
        lat = request.args.get('northing')
    else:
        lat = request.args.get('lat')
    (lon, lat) = validate_lon_lat(lon, lat)

    if 'sr' in request.args:
        sr = int(request.args.get('sr'))
    else:
        point = Point(lon, lat)
        sr = srs_guesser(point)
        if sr is None:
            abort(make_error_msg(400, "No 'sr' given and cannot be guessed from 'geom'"))
    sr = validate_sr(sr)

    if lon < bboxes[sr][0] or lon > bboxes[sr][2] or lat < bboxes[sr][1] or lat > bboxes[sr][3]:
        abort(make_error_msg(400, "Query is out of bounds"))
    alt = get_height(sr, lon, lat, georaster_utils)
    if alt is None:
        abort(
            make_error_msg(
                400, 'Requested coordinate ({},{}) out of bounds in sr {}'.format(lon, lat, sr)
            )
        )
    return {'height': str(alt)}


@app.route('/profile.json', methods=['GET', 'POST'])
def profile_json_route():
    return __get_profile_from_helper(request, True)


@app.route('/profile.csv', methods=['GET', 'POST'])
def profile_csv_route():
    return __get_profile_from_helper(request, False)


def __get_profile_from_helper(request_object, output_to_json=True):
    linestring = profile_arg_validation.read_linestring(request_object)
    nb_points = profile_arg_validation.read_number_points(request_object)
    is_custom_nb_points = profile_arg_validation.read_is_custom_nb_points(request_object)
    spatial_reference = profile_arg_validation.read_spatial_reference(request_object, linestring)
    offset = profile_arg_validation.read_offset(request_object)

    # param only_requested_points, which is flag that when set to True will make
    # the profile with only the given points in geom (no filling points)
    if 'only_requested_points' in request_object.args:
        only_requested_points = bool(request_object.args.get('only_requested_points'))
    else:
        only_requested_points = False

    # flag that define if filling has to be smart, aka to take resolution into account (so that
    # there's not two points closer than what the resolution is) or if points are placed without
    # care for that.
    if 'smart_filling' in request_object.args:
        smart_filling = bool(request_object.args.get('smart_filling'))
    else:
        smart_filling = False

    if 'distinct_points' in request_object.args:
        keep_points = bool(request_object.args.get('distinct_points'))
    else:
        keep_points = False

    result = get_profile(
        geom=linestring,
        spatial_reference=spatial_reference,
        nb_points=nb_points,
        offset=offset,
        only_requested_points=only_requested_points,
        smart_filling=smart_filling,
        keep_points=keep_points,
        output_to_json=output_to_json,
        georaster_utils=georaster_utils
    )
    if output_to_json:
        response = jsonify(result)
    else:
        response = str(result)
    # If profile calculation resulted in a lower number of point than requested (because there's no
    # need to add points closer to each other than the min resolution of 2m), we return HTTP 203 to
    # notify that nb_points couldn't be match.
    status_code = 200
    if is_custom_nb_points and len(result) < nb_points:
        status_code = 203
    content_type = 'application/json' if output_to_json else 'text/csv'
    return response, status_code, {'ContentType': content_type, 'Content-Type': content_type}


# if in debug, we add the route to the statistics page, otherwise it is not visible
if app.debug:

    @app.route('/stats')
    def generate_stats():
        return render_template('statistics.html')

    @app.route('/stats_data')
    def stats_data():
        metadata = load_json("metadata.json")
        return app.response_class(prepare_data(metadata), content_type='application/json')
