# -*- coding: utf-8 -*-

from alti.tests.integration import TestsBase


class TestHeightView(TestsBase):

    def setUp(self):
        super(TestHeightView, self).setUp()
        self.headers = {'X-SearchServer-Authorized': 'true'}

    def test_height_no_sr_asuming_lv03(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000.1', 'northing': '200000.1'}, headers=self.headers, status=200)
        self.assertEqual(resp.json['height'], '560.2')

    def test_height_no_sr_asuming_lv95(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '2600000.1', 'northing': '1200000.1'}, headers=self.headers, status=200)
        self.assertEqual(resp.json['height'], '560.2')

    def test_height_no_sr_using_wrong_coordinates(self):
        self.testapp.get('/rest/services/height', params={'easting': '7.66', 'northing': '46.7'}, headers=self.headers, status=400)

    def test_height_using_unknown_sr(self):
        self.testapp.get('/rest/services/height', params={'easting': '600000.1', 'northing': '200000.1', 'sr': 666}, headers=self.headers, status=400)

    def test_height_mixing_up_coordinates_and_sr(self):
        self.testapp.get('/rest/services/height', params={'easting': '600000.1', 'northing': '200000.1', 'sr': 2056}, headers=self.headers, status=400)

    def test_height_mixing_up_coordinates_and_sr_2(self):
        self.testapp.get('/rest/services/height', params={'easting': '2600000.1', 'northing': '1200000.1', 'sr': 21781}, headers=self.headers, status=400)

    def test_height_lv95_valid(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '2600000.1', 'northing': '1200000.1'}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json['height'], '560.2')

    def test_height_lv95_outofbound(self):
        self.testapp.get('/rest/services/height', params={'easting': '2200000.1', 'northing': '1780000.1'}, headers=self.headers, status=400)

    def test_height_lv03_valid(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000.1', 'northing': '200000.1'}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json['height'], '560.2')

    def test_height_lv03_none(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000', 'northing': '0'}, headers=self.headers, status=400)
        resp.mustcontain("No 'sr' given and cannot be guessed from 'geom'")

    def test_height_lv03_nan(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': 'NaN', 'northing': '200000.1'}, headers=self.headers, status=400)
        resp.mustcontain('Please provide numerical values for the parameter \'easting\'/\'lon\'')
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000', 'northing': 'NaN'}, headers=self.headers, status=400)
        resp.mustcontain('Please provide numerical values for the parameter \'northing\'/\'lat\'')

    def test_height_lv03_valid_with_lonlat(self):
        resp = self.testapp.get('/rest/services/height', params={'lon': '604726.8', 'lat': '195738.1'}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json['height'], '509.4')

    def test_height_lv03_with_dtm2(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '604726.8', 'northing': '195738.1', 'layers': 'DTM2'}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json['height'], '509.5')

    def test_height_lv03_with_dtm2_elevModel(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '604726.8', 'northing': '195738.1', 'elevation_model': 'DTM2'}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json['height'], '509.5')

    def test_height_lv03_with_comb(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000.1', 'northing': '200000.1', 'layers': 'COMB'}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json['height'], '553.6')

    def test_height_lv03_with_comb_elevModel(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000.1', 'northing': '200000.1', 'elevation_model': 'COMB'}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json['height'], '553.6')

    def test_height_lv03_wrong_layer(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000', 'northing': '200000', 'layers': 'TOTO'}, headers=self.headers, status=400)
        resp.mustcontain("Please provide a valid name for the elevation")

    def test_height_lv03_wrong_layer_elevModel(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000', 'northing': '200000', 'elevation_model': 'TOTO'}, headers=self.headers, status=400)
        resp.mustcontain("Please provide a valid name for the elevation")

    def test_height_lv03_wrong_lon_value(self):
        resp = self.testapp.get('/rest/services/height', params={'lon': 'toto', 'northing': '200000'}, headers=self.headers, status=400)
        resp.mustcontain("Please provide numerical values")

    def test_height_lv03_wrong_lat_value(self):
        resp = self.testapp.get('/rest/services/height', params={'lon': '600000', 'northing': 'toto'}, headers=self.headers, status=400)
        resp.mustcontain("Please provide numerical values")

    def test_height_lv03_with_callback_valid(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000', 'northing': '200000', 'callback': 'cb_'}, headers=self.headers, status=200)
        self.assertTrue(resp.content_type == 'application/javascript')
        resp.mustcontain('cb_({')

    def test_height_lv03_miss_northing(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000'}, headers=self.headers, status=400)
        resp.mustcontain("Missing parameter 'northing'/'lat'")

    def test_height_lv03_miss_easting(self):
        resp = self.testapp.get('/rest/services/height', params={'northing': '200000'}, headers=self.headers, status=400)
        resp.mustcontain("Missing parameter 'easting'/'lon'")
