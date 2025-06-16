# -*- coding: utf-8 -*-

from mock import Mock
from mock import patch

from tests.unit_tests.base import BaseRouteTestCase

EAST_LV03, NORTH_LV03 = 632510.0, 170755.0
# LV95
EAST_LV95, NORTH_LV95 = 2632510.0, 1170755.0
# Expected results
HEIGHT_DTM2, HEIGHT_DTM25 = 568.2, 567.6


class TestHeight(BaseRouteTestCase):
    # pylint: disable=too-many-public-methods

    def __test_get(self, params):
        return self.test_instance.get(
            '/rest/services/height', query_string=params, headers=self.headers
        )

    def __prepare_mock_and_test_get(
        self, params, mock_georaster_utils=None, expected_status=200, return_value=HEIGHT_DTM2
    ):
        if not mock_georaster_utils:
            mock_georaster_utils = Mock()
        raster_mock = Mock()
        raster_mock.get_height_for_coordinate.return_value = return_value
        mock_georaster_utils.get_raster.return_value = raster_mock
        response = self.__test_get(params)
        self.check_response(response, expected_status)
        return response

    def __assert_height(self, response, expected_height):
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['height'], str(expected_height))

    @patch('app.routes.georaster_utils')
    def test_do_not_fail_when_no_origin(self, mock_georaster_utils):
        self.headers = {}
        self.__assert_height(
            response=self.__prepare_mock_and_test_get(
                mock_georaster_utils=mock_georaster_utils,
                params={
                    'easting': EAST_LV95, 'northing': NORTH_LV95
                }
            ),
            expected_height=HEIGHT_DTM2
        )

    @patch('app.routes.georaster_utils')
    def test_cache_header(self, mock_georaster_utils):
        response = self.__prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'easting': EAST_LV95, 'northing': NORTH_LV95
            }
        )
        self.assertIn('Cache-Control', response.headers)
        self.assertIn('public', response.headers['Cache-Control'])
        self.assertIn('max-age=', response.headers['Cache-Control'])

    @patch('app.routes.georaster_utils')
    def test_height_no_sr_assuming_lv03(self, mock_georaster_utils):
        self.__assert_height(
            response=self.__prepare_mock_and_test_get(
                mock_georaster_utils=mock_georaster_utils,
                params={
                    'easting': EAST_LV03, 'northing': NORTH_LV03
                }
            ),
            expected_height=HEIGHT_DTM2
        )

    @patch('app.routes.georaster_utils')
    def test_height_no_sr_assuming_lv95(self, mock_georaster_utils):
        self.__assert_height(
            response=self.__prepare_mock_and_test_get(
                mock_georaster_utils=mock_georaster_utils,
                params={
                    'easting': EAST_LV95, 'northing': NORTH_LV95
                }
            ),
            expected_height=HEIGHT_DTM2
        )

    @patch('app.routes.georaster_utils')
    def test_height_no_sr_using_wrong_coordinates(self, mock_georaster_utils):
        self.__prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'easting': '7.66', 'northing': '46.7'
            },
            expected_status=400
        )

    @patch('app.routes.georaster_utils')
    def test_height_using_unknown_sr(self, mock_georaster_utils):
        self.__prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'easting': '600000.1', 'northing': '200000.1', 'sr': 666
            },
            expected_status=400
        )

    @patch('app.routes.georaster_utils')
    def test_height_mixing_up_coordinates_and_sr(self, mock_georaster_utils):
        self.__prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'easting': '600000.1', 'northing': '200000.1', 'sr': 2056
            },
            expected_status=400
        )

    @patch('app.routes.georaster_utils')
    def test_height_mixing_up_coordinates_and_sr_2(self, mock_georaster_utils):
        self.__prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'easting': '2600000.1', 'northing': '1200000.1', 'sr': 21781
            },
            expected_status=400
        )

    @patch('app.routes.georaster_utils')
    def test_height_lv95_valid(self, mock_georaster_utils):
        self.__assert_height(
            response=self.__prepare_mock_and_test_get(
                mock_georaster_utils=mock_georaster_utils,
                params={
                    'easting': EAST_LV95, 'northing': NORTH_LV95
                }
            ),
            expected_height=HEIGHT_DTM2
        )

    @patch('app.routes.georaster_utils')
    def test_height_lv95_outofbound(self, mock_georaster_utils):
        self.__prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'easting': '2200000.1', 'northing': '1780000.1'
            },
            expected_status=400
        )

    @patch('app.routes.georaster_utils')
    def test_height_lv03_valid(self, mock_georaster_utils):
        self.__assert_height(
            response=self.__prepare_mock_and_test_get(
                mock_georaster_utils=mock_georaster_utils,
                params={
                    'easting': EAST_LV03, 'northing': NORTH_LV03
                }
            ),
            expected_height=HEIGHT_DTM2
        )

    @patch('app.routes.georaster_utils')
    def test_height_lv03_none(self, mock_georaster_utils):
        resp = self.__prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'easting': '600000', 'northing': '-100000'
            },
            expected_status=400
        )
        self.assertTrue(
            "No 'sr' given and cannot be guessed from 'geom'" in resp.get_data(as_text=True)
        )

    @patch('app.routes.georaster_utils')
    def test_height_lv03_nan(self, mock_georaster_utils):
        resp = self.__prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'easting': 'NaN', 'northing': '200000.1'
            },
            expected_status=400
        )
        self.assertTrue(
            'Please provide numerical values for the parameter \'easting\'/\'lon\'' in
            resp.get_data(as_text=True)
        )
        resp = self.__prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'easting': '600000', 'northing': 'NaN'
            },
            expected_status=400
        )
        self.assertTrue(
            'Please provide numerical values for the parameter \'northing\'/\'lat\'' in
            resp.get_data(as_text=True)
        )

    @patch('app.routes.georaster_utils')
    def test_height_lv03_valid_with_lonlat(self, mock_georaster_utils):
        self.__assert_height(
            response=self.__prepare_mock_and_test_get(
                mock_georaster_utils=mock_georaster_utils,
                params={
                    'lon': EAST_LV03, 'lat': NORTH_LV03
                }
            ),
            expected_height=HEIGHT_DTM2
        )

    @patch('app.routes.georaster_utils')
    def test_height_lv03_with_comb(self, mock_georaster_utils):
        self.__assert_height(
            response=self.__prepare_mock_and_test_get(
                mock_georaster_utils=mock_georaster_utils,
                params={
                    'easting': EAST_LV03, 'northing': NORTH_LV03, 'sr': 21781
                }
            ),
            expected_height=HEIGHT_DTM2
        )

    @patch('app.routes.georaster_utils')
    def test_height_lv03_with_comb_elev_model(self, mock_georaster_utils):
        self.__assert_height(
            response=self.__prepare_mock_and_test_get(
                mock_georaster_utils=mock_georaster_utils,
                params={
                    'easting': EAST_LV03, 'northing': NORTH_LV03
                }
            ),
            expected_height=HEIGHT_DTM2
        )

    @patch('app.routes.georaster_utils')
    def test_height_lv03_wrong_lon_value(self, mock_georaster_utils):
        resp = self.__prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'lon': 'toto', 'northing': '200000'
            },
            expected_status=400
        )
        self.assertTrue("Please provide numerical values" in resp.get_data(as_text=True))

    @patch('app.routes.georaster_utils')
    def test_height_lv03_wrong_lat_value(self, mock_georaster_utils):
        resp = self.__prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'lon': '600000', 'northing': 'toto'
            },
            expected_status=400
        )
        self.assertTrue("Please provide numerical values" in resp.get_data(as_text=True))

    @patch('app.routes.georaster_utils')
    def test_height_lv03_with_callback_valid(self, mock_georaster_utils):
        resp = self.__prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'easting': EAST_LV03, 'northing': NORTH_LV03, 'callback': 'cb_'
            }
        )
        self.assertEqual(resp.content_type, 'application/javascript')
        self.assertEqual('cb_({"height":"568.2"})', resp.get_data(as_text=True))

    @patch('app.routes.georaster_utils')
    def test_height_lv03_miss_northing(self, mock_georaster_utils):
        resp = self.__prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={'easting': '600000'},
            expected_status=400
        )
        self.assertTrue("Missing parameter 'northing'/'lat'" in resp.get_data(as_text=True))

    @patch('app.routes.georaster_utils')
    def test_height_lv03_miss_easting(self, mock_georaster_utils):
        resp = self.__prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={'northing': '200000'},
            expected_status=400
        )
        self.assertTrue("Missing parameter 'easting'/'lon'" in resp.get_data(as_text=True))
