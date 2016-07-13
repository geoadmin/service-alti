# -*- coding: utf-8 -*-

from pyramid.config import Configurator
from pyramid.events import BeforeRender, NewRequest
from chsdi.subscribers import add_localizer, add_renderer_globals
from pyramid.renderers import JSONP

from chsdi.renderers import EsriJSON, CSVRenderer
from papyrus.renderers import GeoJSON
from chsdi.lib.raster.georaster import init_rasterfiles


def db(request):
    maker = request.registry.dbmaker
    session = maker()

    def cleanup(request):
        session.close()
    request.add_finished_callback(cleanup)

    return session


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    app_version = settings.get('app_version')
    settings['app_version'] = app_version
    config = Configurator(settings=settings)
    config.include('pyramid_mako')

    # init raster files for height/profile and preload COMB file
    init_rasterfiles(settings.get('dtm_base_path'), ['COMB'])

    # configure 'locale' dir as the translation dir for chsdi app
    config.add_translation_dirs('chsdi:locale/')
    config.add_subscriber(add_localizer, NewRequest)
    config.add_subscriber(add_renderer_globals, BeforeRender)

    # renderers
    config.add_mako_renderer('.html')
    config.add_mako_renderer('.js')
    config.add_renderer('jsonp', JSONP(param_name='callback', indent=None, separators=(',', ':')))
    config.add_renderer('geojson', GeoJSON(jsonp_param_name='callback'))
    config.add_renderer('esrijson', EsriJSON(jsonp_param_name='callback'))
    config.add_renderer('csv', CSVRenderer)

    # route definitions
    config.add_route('dev', '/dev')
    config.add_route('profile_json', '/rest/services/profile.json')
    config.add_route('profile_csv', '/rest/services/profile.csv')
    config.add_route('height', '/rest/services/height')

    config.add_route('checker', '/checker')
    config.add_route('checker_dev', '/checker_dev')

    # Some views for specific routes
    config.add_view(route_name='dev', renderer='chsdi:templates/index.mako')

    # static view definitions
    config.add_static_view('static', 'chsdi:static')
    config.add_static_view('images', 'chsdi:static/images')
    config.add_static_view('examples', 'chsdi:static/doc/examples')
    config.add_static_view('vectorStyles', 'chsdi:static/vectorStyles')
    # keep this the last one
    config.add_static_view('/', 'chsdi:static/doc/build')

    # required to find code decorated by view_config
    config.scan(ignore=['chsdi.tests', 'chsdi.models.bod'])
    return config.make_wsgi_app()
