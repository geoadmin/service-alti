import unittest
from mock import patch, Mock

from shapely.geometry import LineString

from alti.lib.profile_helpers import get_profile, PROFILE_DEFAULT_AMOUNT_POINTS

# a fake geom that covers 20m
FAKE_GEOM = LineString([(2600000, 1199980), (2600000, 1200000)])
# fake values that will be fed to the mock raster (start + 20m/2m -> 11 values)
VALUES_FOR_EACH_2M_STEP = [100.0, 102.0, 104.0, 106.0, 104.0, 100.0, 98.0, 102.0, 104.0, 123.456, 100.0]


def fake_get_height_for_coordinate(x, y):
    return VALUES_FOR_EACH_2M_STEP[int(y - 1199980) / 2]


def prepare_mock(mock_get_raster):
    # creating a fake tile that responds with pre defined values
    tile_mock = Mock()
    tile_mock.get_height_for_coordinate = Mock(side_effect=fake_get_height_for_coordinate)
    # create a fake Georaster object
    georaster_mock = Mock()
    georaster_mock.get_tile.return_value = tile_mock
    # link this to the get_raster function
    mock_get_raster.return_value = georaster_mock


class TestProfileHelpers(unittest.TestCase):

    def __prepare_mock_and_test(self, mock, smart_filling):
        prepare_mock(mock)
        response = get_profile(geom=FAKE_GEOM,
                               spatial_reference=2056,
                               layers=['COMB'],
                               offset=0,
                               only_requested_points=False,
                               smart_filling=smart_filling,
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
        # checking values, it should switch to the next value every 200 / 20 iteration
        for i in range(len(response)):
            self.assertEqual(response[i]['alts']['COMB'], VALUES_FOR_EACH_2M_STEP[i / 10])

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
