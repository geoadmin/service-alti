from alti.lib.helpers import filter_altitude
from alti.lib.raster.georaster import get_raster
import logging

def get_height(spatial_reference, easting, northing):
    raster = get_raster(spatial_reference)
    logging.debug(raster)
    if raster is None:
        return None
    altitude = raster.get_height_for_coordinate(easting, northing)
    logging.debug(altitude)
    return filter_altitude(altitude)
