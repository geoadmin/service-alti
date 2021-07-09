import logging
import os
import re
import time

from flask import Flask
from flask import abort
from flask import g
from flask import request

from app.helpers import make_error_msg
from app.helpers.raster.georaster import GeoRasterUtils
from app.helpers.url import ALLOWED_DOMAINS_PATTERN
from app.middleware import ReverseProxy
from app.settings import DTM_BASE_PATH

logger = logging.getLogger(__name__)
route_logger = logging.getLogger('app.routes')

# Standard Flask application initialisation
app = Flask(__name__)
app.wsgi_app = ReverseProxy(app.wsgi_app, script_name='/')

# init raster files for height/profile and preload COMB file
if not os.path.exists(DTM_BASE_PATH):
    error_message = f"DTM base path points to a none existing folder {DTM_BASE_PATH}"
    logger.error(error_message)
    raise FileNotFoundError(error_message)

georaster_utils = GeoRasterUtils()


# NOTE it is better to have this method registered first (before validate_origin) otherwise
# the route might not be logged if another method reject the request.
@app.before_request
def log_route():
    g.setdefault('request_started', time.time())
    route_logger.info('%s %s', request.method, request.path)


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


# NOTE it is better to have this method registered last (after add_cors_header) otherwise
# the response might not be correct (e.g. headers added in another after_request hook).
@app.after_request
def log_response(response):
    route_logger.info(
        "%s %s - %s",
        request.method,
        request.path,
        response.status,
        extra={
            'response':
                {
                    "status_code": response.status_code,
                    "headers": dict(response.headers.items()),
                },
            "duration": time.time() - g.get('request_started', time.time())
        },
    )
    return response


from app import routes  # pylint: disable=wrong-import-position


def main():
    georaster_utils.init_raster_files(DTM_BASE_PATH, [2056, 21781])
    app.run()


if __name__ == '__main__':
    """
    Entrypoint for the application. At the moment, we do nothing specific, but there might be
    preparatory steps in the future
    """
    main()
