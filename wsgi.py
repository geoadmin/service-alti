import multiprocessing

from gunicorn.app.base import BaseApplication

from app import app as application
from app.helpers import get_logging_cfg
from app.settings import ALTI_WORKERS
from app.settings import HTTP_PORT


class StandaloneApplication(BaseApplication):  # pylint: disable=abstract-method

    def __init__(self, app, options=None):  # pylint: disable=redefined-outer-name
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value for key,
            value in self.options.items() if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


# We use the port 5000 as default, otherwise we set the HTTP_PORT env variable within the container.
if __name__ == '__main__':
    if ALTI_WORKERS <= 0:
        ALTI_WORKERS = (multiprocessing.cpu_count() * 2) + 1
    # Bind to 0.0.0.0 to let your app listen to all network interfaces.
    options = {
        'bind': f'0.0.0.0:{HTTP_PORT}',
        'worker_class': 'gevent',
        'workers': ALTI_WORKERS,
        'access_log_format': '%(h)s %(l)s %(u)s "%(r)s" %(s)s %(B)s Bytes '
                             '"%(f)s" "%(a)s" %(L)ss',
        'timeout': 60,
        'logconfig_dict': get_logging_cfg()
    }
    StandaloneApplication(application, options).run()
