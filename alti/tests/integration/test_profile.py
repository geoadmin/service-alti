# -*- coding: utf-8 -*-

import json
import random
from shapely.geometry import Point, LineString, mapping
from alti.tests.integration import TestsBase
from alti.views.profile import PROFILE_MAX_AMOUNT_POINTS, PROFILE_DEFAULT_AMOUNT_POINTS


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


ENDPOINT_FOR_JSON_PROFILE = '/rest/services/profile.json'
ENDPOINT_FOR_CSV_PROFILE = '/rest/services/profile.csv'

LINESTRING_VALID_LV03 = '{\"type\":\"LineString\",\"coordinates\":[[630000, 170000],[634000, 173000],[631000, 173000]]}'

LINESTRING_VALID_LV95 = '{"type":"LineString","coordinates":[[2629499.8,1170351.9],[2635488.4,1173402.0]]}'
LINESTRING_SMALL_LINE_LV03 = '{"type":"LineString","coordinates":[[632092.11, 171171.07],[632084.41, 171237.67]]}'
LINESTRING_SMALL_LINE_LV95 = '{"type":"LineString","coordinates":[[2632092.1,1171169.9],[2632084.4,1171237.3]]}'
LINESTRING_WRONG_SHAPE = '{"type":"OneShape","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}'
LINESTRING_MISSPELLED_SHAPE = '{"type":"OneShape","coordinates":[[550050,206550],[556950,204150],[561050,207950]]'


class TestProfileView(TestsBase):

    def __get_json_profile(self, params, expected_status):
        return self.testapp.get(ENDPOINT_FOR_JSON_PROFILE,
                                params=params,
                                headers=self.headers,
                                status=expected_status)

    def __get_csv_with_params(self, params, expected_status):
        return self.testapp.get(ENDPOINT_FOR_CSV_PROFILE,
                                params=params,
                                headers=self.headers,
                                status=expected_status)

    def __post_with_body(self, body, expected_status):
        return self.testapp.post(ENDPOINT_FOR_JSON_PROFILE,
                                 body,
                                 headers=self.headers,
                                 status=expected_status)

    def setUp(self):
        super(TestProfileView, self).setUp()
        self.headers = {'X-SearchServer-Authorized': 'true'}

    def test_profile_no_sr_json_valid(self):
        self.__get_json_profile(params={'geom': create_json(3, 21781)},
                                expected_status=200)

    def test_profile_invalid_sr_json_valid(self):
        resp = self.__get_json_profile(params={'sr': 666, 'geom': create_json(3, 21781)},
                                       expected_status=400)
        resp.mustcontain("Please provide a valid number for the spatial reference system model 21781 or 2056")

    def test_profile_lv95_json_valid(self):
        self.__get_json_profile(params={'sr': 2056, 'geom': create_json(4, 2056)},
                                expected_status=200)

    def test_profile_lv03_json_valid(self):
        resp = self.__get_json_profile(params={'geom': LINESTRING_VALID_LV03},
                                       expected_status=200)
        self.assertEqual(resp.content_type, 'application/json')
        first_point = resp.json[0]
        self.assertEqual(first_point['dist'], 0)
        self.assertEqual(first_point['alts']['COMB'], 567.3)
        self.assertEqual(first_point['easting'], 630000)
        self.assertEqual(first_point['northing'], 170000)
        second_point = resp.json[1]
        self.assertEqual(second_point['dist'], 40.4)
        self.assertEqual(second_point['alts']['COMB'], 568.5)
        self.assertEqual(second_point['easting'], 630032.323)
        self.assertEqual(second_point['northing'], 170024.242)

    def test_profile_lv03_json_2_models(self):
        resp = self.__get_json_profile(params={'geom': LINESTRING_VALID_LV03,
                                               'elevation_models': 'DTM25,DTM2'},
                                       expected_status=200)
        self.assertEqual(resp.content_type, 'application/json')
        second_point = resp.json[1]
        self.assertEqual(second_point['dist'], 40.4)
        self.assertEqual(second_point['alts']['DTM25'], 568.4)
        self.assertEqual(second_point['alts']['DTM2'], 568.5)
        self.assertEqual(second_point['easting'], 630032.323)
        self.assertEqual(second_point['northing'], 170024.242)

    def test_profile_lv03_layers(self):
        resp = self.__get_json_profile(params={'geom': create_json(4, 21781),
                                               'layers': 'DTM25,DTM2'},
                                       expected_status=200)
        self.assertEqual(resp.content_type, 'application/json')

    def test_profile_lv03_layers_post(self):
        params = {'geom': create_json(4, 21781),
                  'layers': 'DTM25,DTM2'}
        content_type, body = self.testapp.encode_multipart(params.iteritems(), [])
        self.headers['Content-Type'] = str(content_type)
        resp = self.__post_with_body(body=body, expected_status=200)
        self.assertEqual(resp.content_type, 'application/json')

    def test_profile_lv03_layers_none(self):
        resp = self.__get_json_profile(params={'geom': '{"type":"LineString","coordinates":[[0,0],[0,0],[0,0]]}',
                                               'layers': 'DTM25,DTM2'},
                                       expected_status=400)
        resp.mustcontain("No 'sr' given and cannot be guessed from 'geom'")

    def test_profile_lv03_layers_none2(self):
        resp = self.__get_json_profile(params={'geom': '{"type":"LineString","coordinates":[[550050,-206550],[556950,204150],[561050,207950]]}',
                                               'layers': 'DTM25,DTM2'},
                                       expected_status=400)
        resp.mustcontain("No 'sr' given and cannot be guessed from 'geom'")

    def test_profile_lv03_json_2_models_notvalid(self):
        resp = self.__get_json_profile(params={'geom': create_json(4, 21781),
                                               'elevation_models': 'DTM25,DTM222'},
                                       expected_status=400)
        resp.mustcontain('Please provide a valid name for the elevation model DTM25, DTM2 or COMB')

    def test_profile_lv03_json_with_callback_valid(self):
        resp = self.__get_json_profile(params={'geom': create_json(4, 21781),
                                               'callback': 'cb_'},
                                       expected_status=200)
        self.assertEqual(resp.content_type, 'application/javascript')
        resp.mustcontain('cb_([')

    def test_profile_lv03_json_missing_geom(self):
        resp = self.__get_json_profile(params=None, expected_status=400)
        resp.mustcontain('Missing parameter geom')

    def test_profile_lv03_json_wrong_geom(self):
        resp = self.__get_json_profile(params={'geom': 'toto'},
                                       expected_status=400)
        resp.mustcontain('Error loading geometry in JSON string')

    def test_profile_lv03_json_wrong_shape(self):
        resp = self.__get_json_profile(params={'geom': LINESTRING_WRONG_SHAPE},
                                       expected_status=400)
        resp.mustcontain('Error converting JSON to Shape')

    def test_profile_lv03_json_nb_points(self):
        # as 150 is too much for this profile (distance between points will be smaller than 2m resolution of the
        # altitude model), the service will return 203 and a smaller amount of points
        resp = self.__get_json_profile(params={'geom': LINESTRING_SMALL_LINE_LV03,
                                               'nb_points': '150'},
                                       expected_status=203)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertNotEqual(len(resp.json), 150)

    def test_profile_lv03_json_simplify_linestring(self):
        resp = self.__get_json_profile(params={'geom': create_json(4, 21781),
                                               'nb_points': '2'},
                                       expected_status=200)
        self.assertEqual(resp.content_type, 'application/json')

    def test_profile_lv03_json_nbPoints(self):
        resp = self.__get_json_profile(params={'geom': LINESTRING_SMALL_LINE_LV03,
                                               'nbPoints': '150'},
                                       expected_status=203)

        self.assertEqual(resp.content_type, 'application/json')

    def test_profile_lv03_json_nb_points_wrong(self):
        resp = self.__get_json_profile(params={'geom': create_json(4, 21781),
                                               'nb_points': 'toto'},
                                       expected_status=400)
        resp.mustcontain("Please provide a numerical value for the parameter 'NbPoints'/'nb_points'")

    def test_profile_lv03_json_nb_points_too_much(self):
        resp = self.__get_json_profile(params={'geom': create_json(4, 21781),
                                               'nb_points': PROFILE_MAX_AMOUNT_POINTS + 1},
                                       expected_status=400)
        resp.mustcontain("Please provide a numerical value for the parameter 'NbPoints'/'nb_points'")

    def test_profile_lv03_json_default_nb_points(self):
        resp = self.__get_json_profile(params={'geom': LINESTRING_VALID_LV03},
                                       expected_status=200)
        self.assertEqual(len(resp.json), PROFILE_DEFAULT_AMOUNT_POINTS)
        self.assertLess(len(resp.json), PROFILE_MAX_AMOUNT_POINTS)

    def test_profile_lv03_json_no_more_than_max_nb_points(self):
        params = {'geom': LINESTRING_VALID_LV03}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        pnts = resp.json
        self.assertEqual(len(pnts), PROFILE_DEFAULT_AMOUNT_POINTS)
        self.assertLess(len(pnts), PROFILE_MAX_AMOUNT_POINTS)

    def test_profile_lv03_csv_valid(self):
        resp = self.__get_csv_with_params(params={'geom': create_json(4, 21781)},
                                          expected_status=200)
        self.assertEqual(resp.content_type, 'text/csv')

    def test_profile_lv03_cvs_wrong_geom(self):
        resp = self.__get_csv_with_params(params={'geom': 'toto'},
                                          expected_status=400)
        resp.mustcontain('Error loading geometry in JSON string')

    def test_profile_lv03_csv_misspelled_shape(self):
        resp = self.__get_csv_with_params(params={'geom': LINESTRING_MISSPELLED_SHAPE},
                                          expected_status=400)
        resp.mustcontain('Error loading geometry in JSON string')

        resp = self.__get_csv_with_params(params={'geom': LINESTRING_WRONG_SHAPE},
                                          expected_status=400)
        resp.mustcontain('Error converting JSON to Shape')

    def test_profile_lv03_json_invalid_linestring(self):
        resp = self.__get_json_profile(params={'geom': '{"type":"LineString","coordinates":[[550050,206550]]}'},
                                       expected_status=400)
        resp.mustcontain('Invalid Linestring syntax')

    def test_profile_lv03_json_offset(self):
        resp = self.__get_json_profile(params={'geom': LINESTRING_VALID_LV03,
                                               'offset': '1'},
                                       expected_status=200)
        self.assertTrue(resp.content_type == 'application/json')

    def test_profile_lv03_json_invalid_offset(self):
        resp = self.__get_json_profile(params={'geom': LINESTRING_VALID_LV03,
                                               'offset': 'asdf'},
                                       expected_status=400)
        resp.mustcontain("Please provide a numerical value for the parameter 'offset'")

    def test_profile_entity_too_large(self):
        resp = self.__get_json_profile(params={'geom': create_json(7000),
                                               'sr': '2056'},
                                       expected_status=413)
        resp.mustcontain('LineString too large')

    def test_profile_entity_too_large_post(self):
        params = {'geom': create_json(7000), 'sr': '2056'}
        content_type, body = self.testapp.encode_multipart(params.iteritems(), [])
        self.headers['Content-Type'] = str(content_type)
        resp = self.__post_with_body(body=body, expected_status=413)
        resp.mustcontain('LineString too large')

    def test_profile_lv95(self):
        resp = self.__get_json_profile(params={'geom': LINESTRING_VALID_LV95},
                                       expected_status=200)
        self.assertTrue(resp.content_type == 'application/json')

    def test_profile_lv95_with_resolution_too_big(self):
        resp = self.__get_json_profile(params={'geom': LINESTRING_VALID_LV95,
                                               'resolution': 3},
                                       expected_status=203)
        self.assertTrue(resp.content_type == 'application/json')

    def test_profile_lv95_nb_points_exceeds_resolution_meshing(self):
        resp = self.__get_json_profile(params={'geom': LINESTRING_SMALL_LINE_LV95,
                                               'nb_points': 150},
                                       expected_status=203)
        self.assertTrue(resp.content_type == 'application/json')
