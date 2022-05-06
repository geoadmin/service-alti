import logging
import re
import time

from flask import Flask
from flask import g
from flask import request

from app import settings
from app.helpers import init_logging
from app.helpers.raster.georaster import GeoRasterUtils
from app.helpers.url import ALLOWED_DOMAINS_PATTERN
from app.middleware import ReverseProxy

# Initialize Logging using JSON format for all loggers and using the Stream Handler.
init_logging()

logger = logging.getLogger(__name__)
route_logger = logging.getLogger('app.routes')

# Standard Flask application initialisation
app = Flask(__name__)
app.config.from_object(settings)
app.wsgi_app = ReverseProxy(app.wsgi_app, script_name='/')

# init raster files for height/profile and preload COMB file
georaster_utils = GeoRasterUtils()


# NOTE it is better to have this method registered first (before validate_origin) otherwise
# the route might not be logged if another method reject the request.
@app.before_request
def log_route():
    g.setdefault('request_started', time.time())
    route_logger.debug('%s %s', request.method, request.path)


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


from app import routes  # isort:skip pylint: disable=wrong-import-position
