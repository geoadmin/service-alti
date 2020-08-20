from app.helpers.helpers import filter_altitude


def get_height(spatial_reference, easting, northing, georaster_utils):
    raster = georaster_utils.get_raster(spatial_reference)
    if raster is None:
        return None
    altitude = raster.get_height_for_coordinate(easting, northing)
    return filter_altitude(altitude)
