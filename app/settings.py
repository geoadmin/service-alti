import os
from pathlib import Path


def strtobool(value):
    """Convert a string representation of truth to True or False.

    Replaces deprecated https://github.com/python/cpython/blob/3.10/Lib/distutils/util.py#L308
    """
    value = value.lower()
    if value in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    if value in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    raise ValueError(f"invalid truth value {value!r}")


BASE_DIR = Path(__file__).parent.parent.resolve(strict=True)

HTTP_PORT = str(os.getenv('HTTP_PORT', "5000"))
ALTI_WORKERS = int(os.getenv('ALTI_WORKERS', '0'))
LOGS_DIR = os.getenv('LOGS_DIR', str(BASE_DIR / 'logs'))
os.environ['LOGS_DIR'] = LOGS_DIR  # Set default if not set
LOGGING_CFG = os.getenv('LOGGING_CFG', 'logging-cfg-local.yml')

DTM_BASE_PATH = Path(os.getenv('DTM_BASE_PATH', '/var/local/profile/'))
PRELOAD_RASTER_FILES = strtobool(os.getenv('PRELOAD_RASTER_FILES', 'False'))
DFT_CACHE_HEADER = os.getenv('DFT_CACHE_HEADER', 'public, max-age=86400')

TRAP_HTTP_EXCEPTIONS = True

VALID_SRID = [21781, 2056]
GUNICORN_WORKER_TMP_DIR = os.getenv("GUNICORN_WORKER_TMP_DIR", None)
GUNICORN_KEEPALIVE = int(os.getenv("GUNICORN_KEEPALIVE", '2'))
