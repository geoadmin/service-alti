from alti.lib.helpers import filter_altitude
from alti.lib.raster.georaster import get_raster

import logging
log = logging.getLogger('alti')


def get_height(spatial_reference, easting, northing):
    raster = get_raster(spatial_reference)
    if raster is None:
        return None
    altitude = raster.get_height_for_coordinate(easting, northing)
    log.debug("northing: {}, easting: {} => altitude: {}".format(northing, easting, altitude))
    return filter_altitude(altitude)
