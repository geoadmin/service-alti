# -*- coding: utf-8 -*-
from mock import Mock
from shapely.geometry import LineString

# a fake geom that covers 20m
FIRST_POINT = (2600000, 1199980)
MIDDLE_POINT = (2600000, 1199981)
LAST_POINT = (2600000, 1200000)
FAKE_GEOM_2_POINTS = LineString([FIRST_POINT, LAST_POINT])
FAKE_GEOM_3_POINTS = LineString([FIRST_POINT, MIDDLE_POINT, LAST_POINT])
# fake values that will be fed to the mock raster (start + 20m/2m -> 11 values)
FAKE_RESOLUTION = 2.0
VALUES_FOR_EACH_2M_STEP = [
    100.0, 102.0, 104.0, 106.0, 104.0, 100.0, 98.0, 102.0, 104.0, 123.456, 100.0
]

ENDPOINT_FOR_JSON_PROFILE = '/rest/services/profile.json'
ENDPOINT_FOR_CSV_PROFILE = '/rest/services/profile.csv'
DEFAULT_HEADERS = {'Origin': 'https://map.geo.admin.ch'}

POINT_1_LV03 = [630000, 170000]
POINT_2_LV03 = [634000, 173000]
POINT_3_LV03 = [631000, 173000]
LINESTRING_VALID_LV03 = f'{{"type":"LineString","coordinates":[{POINT_1_LV03},{POINT_2_LV03},' \
                        f'{POINT_3_LV03}]}}'

LINESTRING_VALID_LV95 = '{"type":"LineString","coordinates":[[2629499.8,1170351.9],' \
                        '[2635488.4,1173402.0]]}'
LINESTRING_SMALL_LINE_LV03 = '{"type":"LineString","coordinates":[[632092.11, 171171.07],' \
                             '[632084.41, 171237.67]]}'
LINESTRING_SMALL_LINE_LV95 = '{"type":"LineString","coordinates":[[2632092.1,1171169.9],' \
                             '[2632084.4,1171237.3]]}'
LINESTRING_WRONG_SHAPE = '{"type":"OneShape","coordinates":[[550050,206550],[556950,204150],' \
                         '[561050,207950]]}'
LINESTRING_MISSPELLED_SHAPE = '{"type":"OneShape","coordinates":[[550050,206550],[556950,204150],' \
                              '[561050,207950]]'


def fake_get_height_for_coordinate(_, y):
    return VALUES_FOR_EACH_2M_STEP[int(int(y - 1199980) / 2) % 11]


def prepare_mock(mock_georaster_utils):
    # creating a fake tile that responds with pre defined values
    tile_mock = Mock()
    tile_mock.get_height_for_coordinate = Mock(side_effect=fake_get_height_for_coordinate)
    tile_mock.resolution_x.return_value = FAKE_RESOLUTION
    # link this to the get_raster function
    mock_georaster_utils.get_raster.return_value.get_tile.return_value = tile_mock
