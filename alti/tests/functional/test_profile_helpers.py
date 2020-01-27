import unittest
from mock import patch, Mock

from shapely.geometry import LineString

from alti.lib.profile_helpers import get_profile
from alti.lib.validation.profile import PROFILE_DEFAULT_AMOUNT_POINTS

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

    def __prepare_mock_and_test(self,
                                mock,
                                smart_filling,
                                spatial_reference_in=2056,
                                spatial_reference_out=None,
                                geom=FAKE_GEOM):
        prepare_mock(mock)
        response = get_profile(geom=geom,
                               spatial_reference_in=spatial_reference_in,
                               spatial_reference_out=spatial_reference_out,
                               native_srs=2056,
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
        # preparing fake data to be feed to mocks (has to cover overall the same ground as FAKE_GEOM otherwise
        # we would have to prepare another mock tile)
        extra_point_north = 1199981
        extra_point_east = 2600000
        geom_with_multiple_points = LineString([(2600000, 1199980),
                                                (extra_point_east, extra_point_north),
                                                (2600000, 1200000)])
        response = self.__prepare_mock_and_test(mock_get_raster, smart_filling=True, geom=geom_with_multiple_points)
        self.assertEqual(len(response),
                         12,
                         msg="There should be an extra points at (2600000, 1199981) included in the result (even though"
                             "it is closer to other points than the resolution, as it was in geom it must be included")
        # there should be our extra point at index 1, just after the first point
        extra_point = response[1]
        self.assertEqual(extra_point['easting'], extra_point_east)
        self.assertEqual(extra_point['northing'], extra_point_north)

        @patch('alti.lib.profile_helpers.get_raster')
        def test_different_in_out_spatial_references(self, mock_get_raster):
            # output to Web Mercator (EPSG:4326)
            response = self.__prepare_mock_and_test(mock_get_raster,
                                                    geom=geom_with_multiple_points,
                                                    spatial_reference_in=2056,
                                                    spatial_reference_out=4326)
            # checking out that first and last points are in WebMercator format
            first_point = response[0]
            last_point = response[len(response) - 1]
            # [2600000, 1199980] and [2600000, 1200000] to WebMercator translate roughly to
            # ~> [46.9509028684, 7.43863242406] [46.9510827719, 7.43863242087]
            self.assertAlmostEqual(first_point['northing'], 46.9509028684, places=6)
            self.assertAlmostEqual(first_point['easting'], 7.43863242406, places=6)
            self.assertAlmostEqual(last_point['northing'], 46.9510827719, places=6)
            self.assertAlmostEqual(last_point['easting'], 7.43863242087, places=6)
