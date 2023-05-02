import logging
import re
import time
from itertools import chain

from flask import Flask
from flask import g
from flask import request

from app import settings
from app.helpers import init_logging
from app.helpers.raster.georaster import GeoRasterUtils
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
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers['Access-Control-Allow-Headers'] = "*"
    response.headers.set(
        'Access-Control-Allow-Methods', ', '.join(get_registered_method(request.url_rule))
    )
    return response


# Set Cache Headers
@app.after_request
def add_cache_header(response):
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        return response

    # overwrite with these 5xx cache settings
    # no cache on these 5xx errors, they are supposed to be temporary
    if response.status_code in (502, 503, 504, 507):
        response.headers['Cache-Control'] = 'no-cache'
    # short cache duration for other 5xx errors
    elif response.status_code >= 500:
        response.headers['Cache-Control'] = 'public, max-age=10'
    else:
        response.headers['Cache-Control'] = settings.DFT_CACHE_HEADER
    return response


# Helper method for add_cors_header
def get_registered_method(url_rule):
    '''Returns the list of registered method for the given endpoint'''

    # The list of registered method is taken from the werkzeug.routing.Rule. A Rule object
    # has a methods property with the list of allowed method on an endpoint. If this property is
    # missing then all methods are allowed.
    # See https://werkzeug.palletsprojects.com/en/2.0.x/routing/#werkzeug.routing.Rule
    all_methods = ['GET', 'HEAD', 'OPTIONS', 'POST', 'PUT', 'DELETE']
    return set(
        chain.from_iterable(
            [
                r.methods if r.methods else all_methods
                for r in app.url_map.iter_rules()
                if r.rule == str(url_rule)
            ]
        )
    )


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
