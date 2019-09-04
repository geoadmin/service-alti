# -*- coding: utf-8 -*-

import shputils
from os.path import dirname
from struct import unpack

import logging
log = logging.getLogger('alti')

# cache of GeoRaster instances in function of the layer name
_rasters = {}
_rasterfiles = {}


def get_raster(name, sr):
    global _rasters
    filename = "%s%s" % (sr, name)
    result = _rasters.get(filename, None)
    if not result:
        result = GeoRaster(_rasterfiles[sr][name])
        _rasters[filename] = result
        log.debug("GeoRaster for " + repr(filename) + " has been added in the cache")
    return result


def init_rasterfiles(datapath, preloadtypes):
    global _rasterfiles
    # elevation models are :
    # - DTM25 : an old model with a mesh of 25 meters that stretches a little bit outside of Switzerland's borders
    # - DTM2 : a more recent model with a mesh of 2 meters, but doesn't cover a lot of land outside of Switzerland
    # - COMB : a mix of the two, when there's no data on DTM2, DTM25 is requested.
    _rasterfiles = {
        # LV03
        21781: {
            'DTM25': datapath + 'dhm25_25_matrix/mm0001.shp',
            'DTM2': datapath + 'swissalti3d/2m/index.shp',
            'COMB': datapath + 'swissalti3d/kombo_2m_dhm25/index.shp'
        },
        # LV95
        2056: {
            'DTM25': datapath + 'dhm25_25_matrix_lv95/mm0001.shp',
            'DTM2': datapath + 'swissalti3d/2m_lv95/index.shp',
            'COMB': datapath + 'swissalti3d/kombo_2m_dhm25_lv95/index.shp'
        }
        # for other projections, results are reprojected from LV95 model
    }
    try:
        for preloadtype in preloadtypes:
            pt, sr = preloadtype
            get_raster(pt, sr)
            log.info('Preloading raster: %s - %s' % (pt, sr))

    except Exception as e:
        log.error('Could not initialize raster files. Make sure they exist in the following directory: %s (Exception: %s)' % (datapath, e))


class BinaryTerrainTile(object):

    def __init__(self, min_x, min_y, max_x, max_y, filename):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

        self.filename = filename
        self.file = None
        self.first_reading = True

        self.cols = None
        self.rows = None
        self.data_size = None
        self.floating_point = None
        self.resolution_x = None
        self.resolution_y = None

    def __del__(self):
        self.close_file()

    def __str__(self):
        return "%f, %f, %f, %f: %s" % (self.min_x, self.min_y, self.max_x, self.max_y, self.filename)

    def __open_file__(self):
        if self.file is None or self.file.closed:
            self.file = open(self.filename, 'rb')

    def close_file(self):
        if self.file is not None and not self.file.closed:
            self.file.close()

    def contains(self, x, y):
        return self.min_x <= x < self.max_x and self.min_y <= y < self.max_y

    def get_height_for_coordinate(self, x, y):
        # opening file
        self.__open_file__()
        # Reading file metadata if it's the first time reading it
        if self.first_reading:
            self.file.seek(10)
            (self.cols, self.rows, self.data_size, self.floating_point) = unpack('<LLhh', self.file.read(12))
            self.resolution_x = (self.max_x - self.min_x) / self.cols
            self.resolution_y = (self.max_y - self.min_y) / self.rows
            self.first_reading = False
        position_x = int((x - self.min_x) / self.resolution_x)
        position_y = int((y - self.min_y) / self.resolution_y)
        self.file.seek(256 + (position_y + position_x * self.rows) * self.data_size)
        if self.floating_point == 1:
            format_to_unpack = "<f"
        else:
            if self.data_size == 2:
                format_to_unpack = "<h"
            else:
                format_to_unpack = "<l"
        return unpack(format_to_unpack, self.file.read(self.data_size))[0]
        # we let the file opened, so that we can read further point more efficiently
        # (the file will be closed by a call to close_file() or by the __del__ function)


class GeoRaster:

    def __init__(self, index_file):
        self.tiles = []
        directory_name = dirname(index_file)
        if directory_name == "":
            directory_name = "."
        for shape in shputils.loadShapefile(index_file):
            filename = shape['dbf_data']['location'].rstrip()
            if not filename.startswith("/"):
                filename = directory_name + '/' + filename
            if filename.endswith(".bt"):
                geo = shape['shp_data']
                self.tiles.append(BinaryTerrainTile(min_x=geo['xmin'],
                                                    max_x=geo['xmax'],
                                                    min_y=geo['ymin'],
                                                    max_y=geo['ymax'],
                                                    filename=filename))
            else:
                message = ".bt file referenced in index file " + repr(index_file) + " not found, aborting"
                log.error(message)
                raise ValueError(message)

    def get_height_for_coordinate(self, x, y):
        tile = self.get_tile(x, y)
        if tile:
            return tile.get_height_for_coordinate(x, y)
        else:
            return None

    def get_tile(self, x, y):
        for tile in self.tiles:
            if tile.contains(x, y):
                return tile
        return None
