# -*- coding: utf-8 -*-

from alti.tests.integration import TestsBase

# LVO3
EAST_LV03, NORTH_LV03 = '632510.0', '170755.0'
# LV95
EAST_LV95, NORTH_LV95 = '2632510.0', '1170755.0'
# Expected results
HEIGHT_DTM2, HEIGHT_DTM25 = '568.2', '567.6'


class TestHeightView(TestsBase):

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

    def test_height_no_sr_assuming_lv03(self):
        self.__assert_height(response=self.__test_get(params={'easting': EAST_LV03, 'northing': NORTH_LV03}),
                             expected_height=HEIGHT_DTM25)

    def test_height_no_sr_assuming_lv95(self):
        self.__assert_height(response=self.__test_get(params={'easting': EAST_LV95, 'northing': NORTH_LV95}),
                             expected_height=HEIGHT_DTM25)

    def test_height_no_sr_using_wrong_coordinates(self):
        self.__test_get(params={'easting': '7.66', 'northing': '46.7'},
                        expected_status=400)

    def test_height_using_unknown_sr(self):
        self.__test_get(params={'easting': '600000.1', 'northing': '200000.1', 'sr': 666},
                        expected_status=400)

    def test_height_mixing_up_coordinates_and_sr(self):
        self.__test_get(params={'easting': '600000.1', 'northing': '200000.1', 'sr': 2056},
                        expected_status=400)

    def test_height_mixing_up_coordinates_and_sr_2(self):
        self.__test_get(params={'easting': '2600000.1', 'northing': '1200000.1', 'sr': 21781},
                        expected_status=400)

    def test_height_lv95_valid(self):
        self.__assert_height(response=self.__test_get(params={'easting': EAST_LV95, 'northing': NORTH_LV95}),
                             expected_height=HEIGHT_DTM25)

    def test_height_lv95_outofbound(self):
        self.__test_get(params={'easting': '2200000.1', 'northing': '1780000.1'},
                        expected_status=400)

    def test_height_lv03_valid(self):
        self.__assert_height(response=self.__test_get(params={'easting': EAST_LV03, 'northing': NORTH_LV03}),
                             expected_height=HEIGHT_DTM25)

    def test_height_lv03_none(self):
        resp = self.__test_get(params={'easting': '600000', 'northing': '0'},
                               expected_status=400)
        resp.mustcontain("No 'sr' given and cannot be guessed from 'geom'")

    def test_height_lv03_nan(self):
        resp = self.__test_get(params={'easting': 'NaN', 'northing': '200000.1'},
                               expected_status=400)
        resp.mustcontain('Please provide numerical values for the parameter \'easting\'/\'lon\'')
        resp = self.__test_get(params={'easting': '600000', 'northing': 'NaN'},
                               expected_status=400)
        resp.mustcontain('Please provide numerical values for the parameter \'northing\'/\'lat\'')

    def test_height_lv03_valid_with_lonlat(self):
        self.__assert_height(response=self.__test_get(params={'lon': EAST_LV03, 'lat': NORTH_LV03}),
                             expected_height=HEIGHT_DTM25)

    def test_height_lv03_with_comb(self):
        self.__assert_height(response=self.__test_get(params={'easting': EAST_LV03, 'northing': NORTH_LV03}),
                             expected_height=HEIGHT_DTM2)

    def test_height_lv03_with_comb_elevModel(self):
        self.__assert_height(response=self.__test_get(params={'easting': EAST_LV03, 'northing': NORTH_LV03}),
                             expected_height=HEIGHT_DTM2)


    def test_height_lv03_wrong_lon_value(self):
        resp = self.__test_get(params={'lon': 'toto', 'northing': '200000'},
                               expected_status=400)
        resp.mustcontain("Please provide numerical values")

    def test_height_lv03_wrong_lat_value(self):
        resp = self.__test_get(params={'lon': '600000', 'northing': 'toto'},
                               expected_status=400)
        resp.mustcontain("Please provide numerical values")

    def test_height_lv03_with_callback_valid(self):
        resp = self.__test_get(params={'easting': EAST_LV03, 'northing': NORTH_LV03, 'callback': 'cb_'})
        self.assertTrue(resp.content_type == 'application/javascript')
        resp.mustcontain('cb_({')

    def test_height_lv03_miss_northing(self):
        resp = self.__test_get(params={'easting': '600000'},
                               expected_status=400)
        resp.mustcontain("Missing parameter 'northing'/'lat'")

    def test_height_lv03_miss_easting(self):
        resp = self.__test_get(params={'northing': '200000'},
                               expected_status=400)
        resp.mustcontain("Missing parameter 'easting'/'lon'")
