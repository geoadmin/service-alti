from alti.lib.helpers import filter_altitude
from alti.lib.raster.georaster import get_raster


def get_height(spatial_reference, easting, northing):
    raster = get_raster(spatial_reference)
    if raster is None:
        return None
    altitude = raster.get_height_for_coordinate(easting, northing)
    return filter_altitude(altitude)
