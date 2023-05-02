import os
from distutils.util import strtobool
from pathlib import Path

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
