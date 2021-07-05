# -*- coding: utf-8 -*-
import logging
from os.path import dirname
from struct import unpack

from .shputils import SHPUtils

log = logging.getLogger(__name__)

RESOLUTION = 2


class GeoRasterUtils(object):

    def __init__(self):
        self.shp_utils = SHPUtils()
        self.raster = {}
        self.raster_files = {}

    def get_raster(self, sr):
        result = self.raster.get(sr, None)
        if result is None:
            index_file = self.raster_files[sr]
            result = GeoRaster(index_file, self.shp_utils.load_shape_file(index_file))
            self.raster[sr] = result
            log.debug("GeoRaster for %s has been added in the cache", repr(sr))
        return result

    def init_raster_files(self, data_path, supported_spatial_references):
        self.raster_files = {
            # LV03
            21781: data_path + 'swissalti3d/kombo_2m_regio/index.shp',  # LV95
            2056: data_path + 'swissalti3d/kombo_2m_regio_lv95/index.shp'
            # for other projections, results are reprojected from LV95 model
        }
        try:
            # this is currently the same as doing it for all raster_files, but if we support one day
            # another projection and don't want to preload it, we have the possibility to do so.
            for sr in supported_spatial_references:
                self.get_raster(sr)
                log.info('Preloading raster for spatial reference: %s', sr)

        # pylint: disable=broad-except
        except Exception as e:
            log.error(
                'Could not initialize raster files. Make sure they exist in the following '
                'directory: %s (Exception: %s)',
                data_path,
                e
            )
            raise e


class BinaryTerrainTile(object):
    # pylint: disable=too-many-instance-attributes

    def __init__(self, min_x, min_y, max_x, max_y, filename):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

        self.filename = filename
        self.first_reading = True

        self.cols = None
        self.rows = None
        self.data_size = None
        self.floating_point = None
        self.resolution_x = None
        self.resolution_y = None

    def __str__(self):
        return "%f, %f, %f, %f: %s" % (
            self.min_x, self.min_y, self.max_x, self.max_y, self.filename
        )

    def contains(self, x, y):
        return self.min_x <= x < self.max_x and self.min_y <= y < self.max_y

    def get_height_for_coordinate(self, x, y):
        with open(self.filename, 'rb') as file:
            # Reading file metadata if it's the first time reading it
            if self.first_reading:
                file.seek(10)
                (self.cols, self.rows, self.data_size,
                 self.floating_point) = unpack('<LLhh', file.read(12))
                self.resolution_x = (self.max_x - self.min_x) / self.cols
                self.resolution_y = (self.max_y - self.min_y) / self.rows
                self.first_reading = False
            position_x = int((x - self.min_x) / self.resolution_x)
            position_y = int((y - self.min_y) / self.resolution_y)
            file.seek(256 + (position_y + position_x * self.rows) * self.data_size)
            if self.floating_point == 1:
                format_to_unpack = "<f"
            else:
                if self.data_size == 2:
                    format_to_unpack = "<h"
                else:
                    format_to_unpack = "<l"
            return unpack(format_to_unpack, file.read(self.data_size))[0]


class GeoRaster:

    def __init__(self, index_file, shape_files):
        self.tiles = []
        directory_name = dirname(index_file)
        if directory_name == "":
            directory_name = "."
        for shape in shape_files:
            filename = shape['dbf_data']['location'].rstrip()
            if not filename.startswith("/"):
                filename = directory_name + '/' + filename
            if filename.endswith(".bt"):
                geo = shape['shp_data']
                self.tiles.append(
                    BinaryTerrainTile(
                        min_x=geo['xmin'],
                        max_x=geo['xmax'],
                        min_y=geo['ymin'],
                        max_y=geo['ymax'],
                        filename=filename
                    )
                )
            else:
                message = ".bt file referenced in index file " + repr(index_file) \
                          + " not found, aborting"
                log.error(message)
                raise ValueError(message)

    def get_height_for_coordinate(self, x, y):
        tile = self.get_tile(x, y)
        if tile:
            return tile.get_height_for_coordinate(x, y)
        return None

    def get_tile(self, x, y):
        for tile in self.tiles:
            if tile.contains(x, y):
                return tile
        return None
