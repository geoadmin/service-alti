# -*- coding: utf-8 -*-

import json
import random
from shapely.geometry import Point, LineString, mapping
from alti.tests.integration import TestsBase


def generate_random_coord(srid):
    if srid == 2056:
        minx, miny = 2650000, 1200000
        maxx, maxy = 2750000, 1280000
    else:
        minx, miny = 650000, 200000
        maxx, maxy = 750000, 280000
    yield random.randint(minx, maxx), random.randint(miny, maxy)


def generate_random_point(nb_pts, srid):
    for i in xrange(nb_pts):
        for x, y in generate_random_coord(srid):
            yield Point(x, y)


def create_json(nb_pts, srid=2056, json_format=True):
    line = LineString([p for p in generate_random_point(nb_pts, srid)])
    if json_format:
        return json.dumps(mapping(line))
    else:
        return line


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

    def test_profile_lv95_json_same_points(self):
        points_in_profile = 10
        requested_points = points_in_profile
        original_line = create_json(points_in_profile, 2056, json_format=False)
        resp = self.testapp.get('/rest/services/profile.json', params={'nb_points': requested_points, 'sr': 2056, 'geom': json.dumps(mapping(original_line))}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(len(resp.json), points_in_profile)
        x, y = original_line.coords[5]
        c = resp.json[5]
        i, j = c['easting'], c['northing']
        self.assertEqual((x, y), (i, j))

    def test_profile_lv95_json_not_same_points(self):
        points_in_profile = 10
        requested_points = points_in_profile + 10
        original_line = create_json(points_in_profile, 2056, json_format=False)
        resp = self.testapp.get('/rest/services/profile.json', params={'nb_points': requested_points, 'sr': 2056, 'geom': json.dumps(mapping(original_line))}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        x, y = original_line.coords[5]
        c = resp.json[5]
        i, j = c['easting'], c['northing']
        self.assertGreaterEqual(len(resp.json), requested_points)
        self.assertNotEqual((x, y), (i, j))

    def test_profile_lv03_json_valid(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json[0]['dist'], 0)
        self.assertEqual(resp.json[0]['alts']['DTM25'],  1121.7)
        self.assertEqual(resp.json[0]['easting'], 550050)
        self.assertEqual(resp.json[0]['northing'], 206550)

    def test_profile_lv03_json_2_models(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}', 'elevation_models': 'DTM25,DTM2'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json[0]['dist'], 0)
        self.assertEqual(resp.json[0]['alts']['DTM25'],  1121.7)
        self.assertEqual(resp.json[0]['alts']['DTM2'], 1121.9)
        self.assertEqual(resp.json[0]['easting'], 550050)
        self.assertEqual(resp.json[0]['northing'], 206550)

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
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}', 'nb_points': '150'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(len(resp.json), 151)

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
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        pnts = resp.json
        self.assertEqual(len(pnts), 201)

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
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}', 'offset': '1'}
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
