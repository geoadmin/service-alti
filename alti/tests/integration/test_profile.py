# -*- coding: utf-8 -*-

import json
import random
from shapely.geometry import Point, LineString, mapping
from alti.tests.integration import TestsBase


LINESTRING_LV03 = '{"type":"LineString","coordinates":[[630000,170000],[634000,173000],[631000,173000]]}'


def generate_random_coord(srid):
    if srid == 2056:
        minx, miny = 2628750, 1170000
        maxx, maxy = 2637500, 1176000
    else:
        minx, miny = 628750, 170000
        maxx, maxy = 637500, 176000

    yield random.randint(minx, maxx), random.randint(miny, maxy)


def generate_random_point(nb_pts, srid):
    for i in xrange(nb_pts):
        for x, y in generate_random_coord(srid):
            yield Point(x, y)


def create_json(nb_pts, srid=2056):
    line = LineString([p for p in generate_random_point(nb_pts, srid)])
    return json.dumps(mapping(line))


class TestProfileView(TestsBase):

    def setUp(self):
        super(TestProfileView, self).setUp()
        self.headers = {'X-SearchServer-Authorized': 'true'}

    def test_profile_no_sr_json_valid(self):
        self.testapp.get('/rest/services/profile.json', params={'geom': create_json(3, 21781)}, headers=self.headers, status=200)

    def test_profile_invalide_sr_json_valid(self):
        resp = self.testapp.get('/rest/services/profile.json', params={'sr': 666, 'geom': create_json(3, 21781)}, headers=self.headers, status=400)
        resp.mustcontain("Please provide a valid number for the spatial reference system model 21781 or 2056")

    def test_profile_lv95_json_valid(self):
        self.testapp.get('/rest/services/profile.json', params={'sr': 2056, 'geom': create_json(4, 2056)}, headers=self.headers, status=200)

    def test_profile_lv03_json_valid(self):
        params = {'geom': LINESTRING_LV03}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json[0]['dist'], 40)
        self.assertEqual(resp.json[0]['alts']['DTM25'], 568.2)
        self.assertEqual(resp.json[0]['easting'], 630032)
        self.assertEqual(resp.json[0]['northing'], 170024)

    def test_profile_lv03_json_2_models(self):
        params = {'geom': LINESTRING_LV03, 'elevation_models': 'DTM25,DTM2'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json[1]['dist'], 40)
        self.assertEqual(resp.json[1]['alts']['DTM25'], 568.2)
        self.assertEqual(resp.json[1]['alts']['DTM2'], 568.3)
        self.assertEqual(resp.json[1]['easting'], 630032)
        self.assertEqual(resp.json[1]['northing'], 170024)

    def test_profile_lv03_layers(self):
        params = {'geom': create_json(4, 21781), 'layers': 'DTM25,DTM2'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')

    def test_profile_lv03_layers_post(self):
        params = {'geom': create_json(4, 21781), 'layers': 'DTM25,DTM2'}
        content_type, body = self.testapp.encode_multipart(params.iteritems(), [])
        self.headers['Content-Type'] = str(content_type)
        resp = self.testapp.post('/rest/services/profile.json', body, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')

    def test_profile_lv03_layers_none(self):
        params = {'geom': '{"type":"LineString","coordinates":[[0,0],[0,0],[0,0]]}', 'layers': 'DTM25,DTM2'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=400)
        resp.mustcontain("No 'sr' given and cannot be guessed from 'geom'")

    def test_profile_lv03_layers_none2(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,-206550],[556950,204150],[561050,207950]]}', 'layers': 'DTM25,DTM2'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=400)
        resp.mustcontain("No 'sr' given and cannot be guessed from 'geom'")

    def test_profile_lv03_json_2_models_notvalid(self):
        params = {'geom': create_json(4, 21781), 'elevation_models': 'DTM25,DTM222'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=400)
        resp.mustcontain('Please provide a valid name for the elevation model DTM25, DTM2 or COMB')

    def test_profile_lv03_json_with_callback_valid(self):
        params = {'geom': create_json(4, 21781), 'callback': 'cb_'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/javascript')
        resp.mustcontain('cb_([')

    def test_profile_lv03_json_missing_geom(self):
        resp = self.testapp.get('/rest/services/profile.json', headers=self.headers, status=400)
        resp.mustcontain('Missing parameter geom')

    def test_profile_lv03_json_wrong_geom(self):
        params = {'geom': 'toto'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=400)
        resp.mustcontain('Error loading geometry in JSON string')

    def test_profile_lv03_json_wrong_shape(self):
        params = {'geom': '{"type":"OneShape","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=400)
        resp.mustcontain('Error converting JSON to Shape')

    def test_profile_lv03_json_nb_points(self):
        params = {'geom': LINESTRING_LV03, 'nb_points': '150'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(len(resp.json), 150)

    def test_profile_lv03_json_simplify_linestring(self):
        params = {'geom': create_json(4, 21781), 'nb_points': '1'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')

    def test_profile_lv03_json_nbPoints(self):
        params = {'geom': create_json(4, 21781), 'nbPoints': '150'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')

    def test_profile_lv03_json_nb_points_wrong(self):
        params = {'geom': create_json(4, 21781), 'nb_points': 'toto'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=400)
        resp.mustcontain("Please provide a numerical value for the parameter 'NbPoints'/'nb_points'")

    def test_profile_lv03_json_nb_points_too_much(self):
        params = {'geom': create_json(4, 21781), 'nb_points': '1000000'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=400)
        resp.mustcontain("Please provide a numerical value for the parameter 'NbPoints'/'nb_points'")

    def test_profile_lv03_json_default_nb_points(self):
        params = {'geom': LINESTRING_LV03}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        pnts = resp.json
        self.assertEqual(len(pnts), 200)

    def test_profile_lv03_csv_valid(self):
        params = {'geom': create_json(4, 21781)}
        resp = self.testapp.get('/rest/services/profile.csv', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'text/csv')

    def test_profile_lv03_cvs_wrong_geom(self):
        params = {'geom': 'toto'}
        resp = self.testapp.get('/rest/services/profile.csv', params=params, headers=self.headers, status=400)
        resp.mustcontain('Error loading geometry in JSON string')

    def test_profile_lv03_csv_wrong_shape(self):
        params = {'geom': '{"type":"OneShape","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}'}
        resp = self.testapp.get('/rest/services/profile.csv', params=params, headers=self.headers, status=400)
        resp.mustcontain('Error converting JSON to Shape')

    def test_profile_lv03_json_invalid_linestring(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550]]}'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=400)
        resp.mustcontain('Invalid Linestring syntax')

    def test_profile_lv03_json_offset(self):
        params = {'geom': LINESTRING_LV03, 'offset': '1'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertTrue(resp.content_type == 'application/json')

    def test_profile_lv03_json_invalid_offset(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}', 'offset': 'asdf'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=400)
        resp.mustcontain("Please provide a numerical value for the parameter 'offset'")

    def test_profile_entity_too_large(self):
        params = {'geom': create_json(7000), 'sr': '2056'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=413)
        resp.mustcontain('LineString too large')

    def test_profile_entity_too_large_post(self):
        params = {'geom': create_json(7000), 'sr': '2056'}
        content_type, body = self.testapp.encode_multipart(params.iteritems(), [])
        self.headers['Content-Type'] = str(content_type)
        resp = self.testapp.post('/rest/services/profile.json', body, headers=self.headers, status=413)
        resp.mustcontain('LineString too large')
