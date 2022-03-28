import logging

from shapely.geometry import Point
from werkzeug.exceptions import HTTPException

from flask import abort
from flask import jsonify
from flask import make_response
from flask import render_template
from flask import request

import app.helpers.validation.profile as profile_arg_validation
from app import app
from app import georaster_utils
from app.helpers import make_error_msg
from app.helpers.height_helpers import get_height
from app.helpers.profile_helpers import get_profile
from app.helpers.route import prefix_route
from app.helpers.validation import bboxes
from app.helpers.validation import srs_guesser
from app.helpers.validation.height import validate_lon_lat
from app.helpers.validation.height import validate_sr
# add route prefix
from app.statistics.statistics import load_json
from app.statistics.statistics import prepare_data
from app.version import APP_VERSION

app.route = prefix_route(app.route, '/rest/services/')

logger = logging.getLogger(__name__)


@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        logger.error(e)
        return make_error_msg(e.code, e.description)
    logger.exception('Unexpected exception: %s', e)
    return make_error_msg(500, "Internal server error, please consult logs")


@app.route('/checker')
def check():
    return make_response(jsonify({'success': True, 'message': 'OK', 'version': APP_VERSION}))


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
            abort(400, "No 'sr' given and cannot be guessed from 'geom'")
    sr = validate_sr(sr)

    if lon < bboxes[sr][0] or lon > bboxes[sr][2] or lat < bboxes[sr][1] or lat > bboxes[sr][3]:
        abort(400, "Query is out of bounds")
    alt = get_height(sr, lon, lat, georaster_utils)
    if alt is None:
        abort(400, f'Requested coordinate ({lon},{lat}) out of bounds in sr {sr}')
    return {'height': str(alt)}


@app.route('/profile.json', methods=['GET', 'POST'])
def profile_json_route():
    return __get_profile_from_helper(True)


@app.route('/profile.csv', methods=['GET', 'POST'])
def profile_csv_route():
    return __get_profile_from_helper(False)


def __get_profile_from_helper(output_to_json=True):
    linestring = profile_arg_validation.read_linestring()
    nb_points = profile_arg_validation.read_number_points()
    is_custom_nb_points = profile_arg_validation.read_is_custom_nb_points()
    spatial_reference = profile_arg_validation.read_spatial_reference(linestring)
    offset = profile_arg_validation.read_offset()

    # param only_requested_points, which is flag that when set to True will make
    # the profile with only the given points in geom (no filling points)
    if 'only_requested_points' in request.args:
        only_requested_points = bool(request.args.get('only_requested_points'))
    else:
        only_requested_points = False

    # flag that define if filling has to be smart, aka to take resolution into account (so that
    # there's not two points closer than what the resolution is) or if points are placed without
    # care for that.
    if 'smart_filling' in request.args:
        smart_filling = bool(request.args.get('smart_filling'))
    else:
        smart_filling = False

    if 'distinct_points' in request.args:
        keep_points = bool(request.args.get('distinct_points'))
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
