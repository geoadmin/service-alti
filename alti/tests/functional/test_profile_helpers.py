import unittest
from mock import patch, Mock

from shapely.geometry import LineString

from alti.lib.profile_helpers import get_profile, PROFILE_DEFAULT_AMOUNT_POINTS

import logging
logger = logging.getLogger('alti')

# a fake geom that covers 20m
FIRST_POINT = (2600000, 1199980)
MIDDLE_POINT = (2600000, 1199981)
LAST_POINT = (2600000, 1200000)
FAKE_GEOM_2_POINTS = LineString([FIRST_POINT, LAST_POINT])
FAKE_GEOM_3_POINTS = LineString([FIRST_POINT, MIDDLE_POINT, LAST_POINT])
# fake values that will be fed to the mock raster (start + 20m/2m -> 11 values)
FAKE_RESOLUTION = 2.0
VALUES_FOR_EACH_2M_STEP = [100.0, 102.0, 104.0, 106.0, 104.0, 100.0, 98.0, 102.0, 104.0, 123.456, 100.0]


def fake_get_height_for_coordinate(x, y):
    return VALUES_FOR_EACH_2M_STEP[int((y - 1199980) / 2) % 11]


def prepare_mock(mock_get_raster):
    # creating a fake tile that responds with pre defined values
    tile_mock = Mock()
    tile_mock.get_height_for_coordinate = Mock(side_effect=fake_get_height_for_coordinate)
    tile_mock.resolution_x.return_value = FAKE_RESOLUTION
    # link this to the get_raster function
    mock_get_raster.return_value.get_tile.return_value = tile_mock


class TestProfileHelpers(unittest.TestCase):

    def __prepare_mock_and_test(self, mock, smart_filling, keep_points=True, geom=FAKE_GEOM_2_POINTS):
        prepare_mock(mock)
        response = get_profile(geom=geom,
                               spatial_reference=2056,
                               offset=0,
                               only_requested_points=False,
                               smart_filling=smart_filling,
                               keep_points=keep_points,
                               output_to_json=True)
        self.assertIsNotNone(response)
        return response

    @patch('alti.lib.profile_helpers.get_raster')
    def test_no_smart_filling(self, mock_get_raster):
        response = self.__prepare_mock_and_test(mock_get_raster, smart_filling=False)
        self.assertEqual(len(response),
                         PROFILE_DEFAULT_AMOUNT_POINTS,
                         msg="with 'dumb' filling, there should be no regard to resolution and default amount of "
                             "points has to be used (default: {}, actual: {})".format(PROFILE_DEFAULT_AMOUNT_POINTS,
                                                                                      len(response)))
        # checking values, it should switch to the next value every 20 iteration (point in profile)
        # i           : 0 .... 19 20 .... 39 40 .... etc ... 198 199 (exception with the last point)
        # value index : 0 .... 0   1 .... 1   2 .... etc ...  9   10
        for i in range(len(response)):
            value = response[i]['alts']['COMB']
            value_index = 10 if i == 199 else i / 20
            expected_value = round(VALUES_FOR_EACH_2M_STEP[value_index] * 10.0) / 10.0
            self.assertEqual(value,
                             expected_value,
                             msg="Wrong value at index {} (tile index: {}, expected: {}, actual: {}".
                             format(i, value_index, expected_value, value))

    @patch('alti.lib.profile_helpers.get_raster')
    def test_with_smart_filling(self, mock_get_raster):
        response = self.__prepare_mock_and_test(mock_get_raster, smart_filling=True)
        self.assertEqual(len(response),
                         11,
                         msg="with 'smart' filling, there should be no more points than the resolution permits "
                             ", in this case 20m of length with a resolution of 2m => 10points plus starting points "
                             "=> 11 (was: {})".format(len(response)))
        # each values should be present only once, so we can test them in sequence (with the exception of rounding,
        # the value at index 9 should be rounded to the first digit : 123.456 => 123.5)
        for i in range(len(response)):
            value = response[i]['alts']['COMB']
            expected = round(VALUES_FOR_EACH_2M_STEP[i] * 10.0) / 10.0
            self.assertEqual(value,
                             expected,
                             msg="Values don't match at index {} (expected: {}, actual: {})".
                             format(i, expected, value))

    @patch('alti.lib.profile_helpers.get_raster')
    def test_smart_filling_must_keep_points_from_geom(self, mock_get_raster):
        response = self.__prepare_mock_and_test(mock_get_raster, smart_filling=True, keep_points=True,
                                                geom=FAKE_GEOM_3_POINTS)
        self.assertEqual(len(response),
                         12,
                         msg="There should be an extra points at (2600000, 1199981) included in the result (even though"
                             "it is closer to other points than the resolution, as it was in geom it must be included")
        # there should be our middle point at index 1, just after the first point
        extra_point = response[1]
        self.assertEqual(extra_point['easting'], MIDDLE_POINT[0])
        self.assertEqual(extra_point['northing'], MIDDLE_POINT[1])

    @patch('alti.lib.profile_helpers.get_raster')
    def test_coordinates_out_of_bound(self, mock_get_raster):
        # when there's no tile for coordinates (because out of bounds) None is returned for the tile
        # the service should return an empty profile
        mock_get_raster.return_value.get_tile.return_value = None
        try:
            response = get_profile(geom=FAKE_GEOM_2_POINTS,
                                   spatial_reference=2056,
                                   offset=0,
                                   only_requested_points=False,
                                   smart_filling=True,
                                   keep_points=True,
                                   output_to_json=True)
            self.assertIsNotNone(response)
            self.assertEqual(len(response), 0)
        except Exception as e:
            logger.error(e, exc_info=True)
            self.fail("Should return an empty profile without failing with coordinates out of bounds")

    @patch('alti.lib.profile_helpers.get_raster')
    def test_keep_point_without_smart_fill(self, mock_get_raster):
        response = self.__prepare_mock_and_test(mock_get_raster,
                                                smart_filling=False,
                                                keep_points=True,
                                                geom=FAKE_GEOM_3_POINTS)
        self.assertEqual(len(response),
                         PROFILE_DEFAULT_AMOUNT_POINTS,
                         msg="There should be an exactly {} points in the profile, found {}".format(
                             PROFILE_DEFAULT_AMOUNT_POINTS, len(response)))
        # there should be our middle point somewhere in the profile
        middle_point_found = False
        for point in response:
            middle_point_found |= point['easting'] == MIDDLE_POINT[0] and point['northing'] == MIDDLE_POINT[1]
        self.assertTrue(middle_point_found, msg="The middle point should be included in the resulting profile "
                                                "as keep_points was set to true")
