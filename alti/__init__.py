# -*- coding: utf-8 -*-

from pyramid.config import Configurator
from pyramid.renderers import JSONP

from alti.renderers import CSVRenderer
from alti.lib.raster.georaster import init_rasterfiles


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    app_version = settings.get('app_version')
    settings['app_version'] = app_version
    config = Configurator(settings=settings)

    # init raster files for height/profile and preload COMB file
    init_rasterfiles(settings.get('dtm_base_path'), [('COMB', 2056), ('COMB', 21781)])

    # renderers
    config.add_renderer('jsonp', JSONP(param_name='callback', indent=None, separators=(',', ':')))
    config.add_renderer('csv', CSVRenderer)

    # route definitions
    config.add_route('profile_json', '/rest/services/profile.json')
    config.add_route('profile_csv', '/rest/services/profile.csv')
    config.add_route('height', '/rest/services/height')

    config.add_route('checker', '/checker')
    config.add_route('checker_dev', '/checker_dev')

    config.add_static_view('static', 'alti:static')
    config.add_static_view('/', 'alti:static/')
    config.scan()
    return config.make_wsgi_app()
