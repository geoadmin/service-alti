import logging
import os
import re

from flask import Flask
from flask import abort
from flask import request

from app.helpers import make_error_msg
from app.helpers.raster.georaster import GeoRasterUtils
from app.helpers.url import ALLOWED_DOMAINS_PATTERN
from app.middleware import ReverseProxy

DEFAULT_DTM_BASE_PATH = '/var/local/profile/'

logger = logging.getLogger(__name__)

# Standard Flask application initialisation
app = Flask(__name__)
app.wsgi_app = ReverseProxy(app.wsgi_app, script_name='/')

# init raster files for height/profile and preload COMB file
dtm_base_path = os.environ.get('DTM_BASE_PATH', DEFAULT_DTM_BASE_PATH)
if not os.path.exists(dtm_base_path):
    error_message = "DTM base path points to a none existing folder (%s)" % dtm_base_path
    logger.error(error_message)
    raise FileNotFoundError(error_message)

georaster_utils = GeoRasterUtils()


@app.after_request
def wrap_in_callback_if_present(response):
    if "callback" in request.args:
        response.headers['Content-Type'] = 'application/javascript'
        response.data = '%s(%s)' % (request.args.get('callback'), response.get_data(as_text=True))
    return response


# Add CORS Headers to all request
@app.after_request
def add_cors_header(response):
    if (
        'Origin' in request.headers and
        re.match(ALLOWED_DOMAINS_PATTERN, request.headers['Origin'])
    ):
        response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response


# Reject request from non allowed origins
@app.before_request
def validate_origin():
    if (
        'Origin' in request.headers and
        not re.match(ALLOWED_DOMAINS_PATTERN, request.headers['Origin'])
    ):
        logger.error('Origin=%s is not allowed', request.headers['Origin'])
        abort(make_error_msg(403, 'Not allowed'))


from app import routes  # pylint: disable=wrong-import-position


def main():
    georaster_utils.init_raster_files(dtm_base_path, [2056, 21781])
    app.run()


if __name__ == '__main__':
    """
    Entrypoint for the application. At the moment, we do nothing specific, but there might be
    preparatory steps in the future
    """
    main()
