# -*- coding: utf-8 -*-

# file taken from http://indiemaps.com/blog/2008/03/easy-shapefile-loading-in-python/
import logging
from struct import unpack

from . import dbfutils

logger = logging.getLogger(__name__)

XY_POINT_RECORD_LENGTH = 16

RECORD_CLASS = {
    0: 'RecordNull',
    1: 'RecordPoint',
    8: 'RecordMultiPoint',
    3: 'RecordPolyLine',
    5: 'RecordPolygon'
}


def read_record_any(fp, data_type):
    if data_type == 0:
        return read_record_null(fp)
    if data_type == 1:
        return read_record_point(fp)
    if data_type == 8:
        return read_record_multi_point(fp)
    if data_type in (3, 5):
        return read_record_poly_line(fp)
    return False


def read_record_null(_):
    return {}


def read_record_point(fp):
    return {'x': read_and_unpack('d', fp.read(8)), 'y': read_and_unpack('d', fp.read(8))}


def read_record_multi_point(fp):
    data = read_bounding_box(fp)
    data['numpoints'] = read_and_unpack('i', fp.read(4))
    for i in range(0, data['numpoints']):
        data['points'].append(read_record_point(fp))
    return data


def read_record_poly_line(fp):
    data = read_bounding_box(fp)
    data['numparts'] = read_and_unpack('i', fp.read(4))
    data['numpoints'] = read_and_unpack('i', fp.read(4))
    data['parts'] = []
    for i in range(0, data['numparts']):
        data['parts'].append(read_and_unpack('i', fp.read(4)))
    points_initial_index = fp.tell()
    points_read = 0
    for part_index in range(0, data['numparts']):
        data['parts'][part_index] = {}
        data['parts'][part_index]['points'] = []

        check_point = []
        while points_read < data['numpoints']:
            curr_point = read_record_point(fp)
            data['parts'][part_index]['points'].append(curr_point)
            points_read += 1
            if points_read == 0 or check_point == []:
                check_point = curr_point
            elif curr_point == check_point:
                break

    fp.seek(points_initial_index + (points_read * XY_POINT_RECORD_LENGTH))
    return data


def read_bounding_box(fp):
    return {
        'xmin': read_and_unpack('d', fp.read(8)),
        'ymin': read_and_unpack('d', fp.read(8)),
        'xmax': read_and_unpack('d', fp.read(8)),
        'ymax': read_and_unpack('d', fp.read(8))
    }


def read_and_unpack(data_type, data):
    if data == b'':
        return data
    return unpack(data_type, data)[0]


class SHPUtils(object):

    def __init__(self):
        self.db = []

    def load_shape_file(self, file_name):
        records = []
        # open dbf file and get records as a list
        dbf_file = file_name[0:-4] + '.dbf'
        logger.debug('Read DBF file %s', dbf_file)
        with open(dbf_file, 'rb') as dbf:
            self.db = list(dbfutils.dbfreader(dbf))
        logger.debug('DBF file parsed: %d db entries', len(self.db))

        logger.debug('Read file %s', file_name)
        with open(file_name, 'rb') as fp:
            # get basic shapefile configuration
            fp.seek(32)
            read_and_unpack('i', fp.read(4))
            read_bounding_box(fp)

            # fetch Records
            fp.seek(100)
            while True:
                shp_record = self.create_record(fp)
                if shp_record is None:
                    break
                records.append(shp_record)

        return records

    def create_record(self, fp):
        # read header
        record_number = read_and_unpack('>L', fp.read(4))
        if record_number == b'':
            return None
        # content_length = readAndUnpack('>L', fp.read(4))
        read_and_unpack('>L', fp.read(4))
        record_shape_type = read_and_unpack('<L', fp.read(4))

        shp_data = read_record_any(fp, record_shape_type)
        dbf_data = {}
        for i in range(0, len(self.db[record_number + 1])):
            dbf_data[self.db[0][i].decode()] = self.db[record_number + 1][i]

        return {'shp_data': shp_data, 'dbf_data': dbf_data}
