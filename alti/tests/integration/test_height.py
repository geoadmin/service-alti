# -*- coding: utf-8 -*-

from alti.tests.integration import TestsBase

from mock import patch


# LVO3
EAST_LV03, NORTH_LV03 = '632510.0', '170755.0'
# LV95
EAST_LV95, NORTH_LV95 = '2632510.0', '1170755.0'
# Expected results
HEIGHT_DTM2, HEIGHT_DTM25 = '568.2', '567.6'

def prepare_mock(mock_get_raster, return_value):
    mock_get_raster.return_value.get_height_for_coordinate.return_value = return_value

class TestHeightView(TestsBase):

    def __prepare_mock_and_test_get(self, mock,
                                    params,
                                    expected_status = 200,
                                    return_value=HEIGHT_DTM2):
        prepare_mock(mock, return_value=return_value)
        response = self.__test_get(params, expected_status)
        self.assertIsNotNone(response)
        return response

    def __test_get(self, params, expected_status=200):
        return self.testapp.get('/rest/services/height',
                                params=params,
                                headers=self.headers,
                                status=expected_status)

    def __assert_height(self, response, expected_height):
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['height'], expected_height)

    def setUp(self):
        super(TestHeightView, self).setUp()
        self.headers = {'X-SearchServer-Authorized': 'true'}

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_no_sr_assuming_lv03(self, mock_get_raster):
        self.__assert_height(response=self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': EAST_LV03, 'northing': NORTH_LV03}),
                             expected_height=HEIGHT_DTM2)

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_no_sr_assuming_lv95(self, mock_get_raster):
        self.__assert_height(response=self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': EAST_LV95, 'northing': NORTH_LV95}),
                             expected_height=HEIGHT_DTM2)

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_no_sr_using_wrong_coordinates(self, mock_get_raster):
        self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': '7.66', 'northing': '46.7'},
                        expected_status=400)

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_using_unknown_sr(self, mock_get_raster):
        self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': '600000.1', 'northing': '200000.1', 'sr': 666},
                        expected_status=400)

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_mixing_up_coordinates_and_sr(self, mock_get_raster):
        self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': '600000.1', 'northing': '200000.1', 'sr': 2056},
                        expected_status=400)

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_mixing_up_coordinates_and_sr_2(self, mock_get_raster):
        self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': '2600000.1', 'northing': '1200000.1', 'sr': 21781},
                        expected_status=400)

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_lv95_valid(self, mock_get_raster):
        self.__assert_height(response=self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': EAST_LV95, 'northing': NORTH_LV95}),
                             expected_height=HEIGHT_DTM2)

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_lv95_outofbound(self, mock_get_raster):
        self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': '2200000.1', 'northing': '1780000.1'},
                        expected_status=400)

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_lv03_valid(self, mock_get_raster):
        self.__assert_height(response=self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': EAST_LV03, 'northing': NORTH_LV03}),
                             expected_height=HEIGHT_DTM2)

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_lv03_none(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': '600000', 'northing': '0'},
                               expected_status=400)
        resp.mustcontain("No 'sr' given and cannot be guessed from 'geom'")

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_lv03_nan(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': 'NaN', 'northing': '200000.1'},
                               expected_status=400)
        resp.mustcontain('Please provide numerical values for the parameter \'easting\'/\'lon\'')
        resp = self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': '600000', 'northing': 'NaN'},
                               expected_status=400)
        resp.mustcontain('Please provide numerical values for the parameter \'northing\'/\'lat\'')

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_lv03_valid_with_lonlat(self, mock_get_raster):
        self.__assert_height(response=self.__prepare_mock_and_test_get(mock_get_raster, params={'lon': EAST_LV03, 'lat': NORTH_LV03}),
                             expected_height=HEIGHT_DTM2)

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_lv03_with_comb(self, mock_get_raster):
        self.__assert_height(response=self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': EAST_LV03, 'northing': NORTH_LV03}),
                             expected_height=HEIGHT_DTM2)

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_lv03_with_comb_elevModel(self, mock_get_raster):
        self.__assert_height(response=self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': EAST_LV03, 'northing': NORTH_LV03}),
                             expected_height=HEIGHT_DTM2)

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_lv03_wrong_lon_value(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_get(mock_get_raster, params={'lon': 'toto', 'northing': '200000'},
                               expected_status=400)
        resp.mustcontain("Please provide numerical values")

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_lv03_wrong_lat_value(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_get(mock_get_raster, params={'lon': '600000', 'northing': 'toto'},
                               expected_status=400)
        resp.mustcontain("Please provide numerical values")

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_lv03_with_callback_valid(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': EAST_LV03, 'northing': NORTH_LV03, 'callback': 'cb_'})
        self.assertTrue(resp.content_type == 'application/javascript')
        resp.mustcontain('cb_({')

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_lv03_miss_northing(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_get(mock_get_raster, params={'easting': '600000'},
                               expected_status=400)
        resp.mustcontain("Missing parameter 'northing'/'lat'")

    @patch('alti.lib.height_helpers.get_raster')
    def test_height_lv03_miss_easting(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_get(mock_get_raster, params={'northing': '200000'},
                               expected_status=400)
        resp.mustcontain("Missing parameter 'easting'/'lon'")
