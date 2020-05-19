# -*- coding: utf-8 -*-

import json
import random
from shapely.geometry import Point, LineString, mapping
from mock import Mock, patch
from alti.tests.integration import TestsBase
from alti.lib.profile_helpers import PROFILE_MAX_AMOUNT_POINTS, PROFILE_DEFAULT_AMOUNT_POINTS, get_profile


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

POINT_1_LV03 = [630000, 170000]
POINT_2_LV03 = [634000, 173000]
POINT_3_LV03 = [631000, 173000]
LINESTRING_VALID_LV03 = '{\"type\":\"LineString\",\"coordinates\":[' \
                        + str(POINT_1_LV03) + ',' \
                        + str(POINT_2_LV03) + ',' \
                        + str(POINT_3_LV03) + ']}'

LINESTRING_VALID_LV95 = '{"type":"LineString","coordinates":[[2629499.8,1170351.9],[2635488.4,1173402.0]]}'
LINESTRING_SMALL_LINE_LV03 = '{"type":"LineString","coordinates":[[632092.11, 171171.07],[632084.41, 171237.67]]}'
LINESTRING_SMALL_LINE_LV95 = '{"type":"LineString","coordinates":[[2632092.1,1171169.9],[2632084.4,1171237.3]]}'
LINESTRING_WRONG_SHAPE = '{"type":"OneShape","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}'
LINESTRING_MISSPELLED_SHAPE = '{"type":"OneShape","coordinates":[[550050,206550],[556950,204150],[561050,207950]]'


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
    return VALUES_FOR_EACH_2M_STEP[int((y - 1199980) / 2)]


def prepare_mock(mock_get_raster):
    # creating a fake tile that responds with pre defined values
    tile_mock = Mock()
    tile_mock.get_height_for_coordinate = Mock(side_effect=fake_get_height_for_coordinate)
    tile_mock.resolution_x.return_value = FAKE_RESOLUTION
    # link this to the get_raster function
    mock_get_raster.return_value.get_tile.return_value = tile_mock


class TestProfileView(TestsBase):

    def __prepare_mock_and_test_json_profile(self, mock, params, expected_status):
        prepare_mock(mock)
        response = self.__get_json_profile(params, expected_status)
        self.assertIsNotNone(response)
        return response

    def __prepare_mock_and_test_post(self, mock, body, expected_status):
        prepare_mock(mock)
        response = self.__post_with_body(body, expected_status)
        self.assertIsNotNone(response)
        return response

    def __prepare_mock_and_test_csv_profile(self, mock, params, status):
        prepare_mock(mock)
        response = self.__get_csv_with_params(params, status)
        self.assertIsNotNone(response)
        return response

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

    def __verify_point_is_present(self, response, point, msg="point not present"):
        self.assertEquals(response.content_type, "application/json")
        self.assertEqual(len(point), 2, msg="Point must be a [x,y] point")
        present = False
        for profile_point in response.json:
            if point[0] == profile_point['easting'] and point[1] == profile_point['northing']:
                present = True
        self.assertTrue(present, msg=msg)

    def setUp(self):
        super(TestProfileView, self).setUp()
        self.headers = {'X-SearchServer-Authorized': 'true'}

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_invalid_sr_json_valid(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'sr': 666, 'geom': create_json(3, 21781)},
                                                         expected_status=400)
        resp.mustcontain("Please provide a valid number for the spatial reference system model 21781 or 2056")

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv95_json_valid(self, mock_get_raster):
        self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'sr': 2056, 'geom': create_json(4, 2056)},
                                                  expected_status=200)

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_json_valid(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': LINESTRING_VALID_LV03,
                                                                 'smart_filling': True},
                                                         expected_status=200)
        self.assertEqual(resp.content_type, 'application/json')
        first_point = resp.json[0]
        self.assertEqual(first_point['dist'], 0)
        self.assertEqual(first_point['alts']['COMB'], 567.3)
        self.assertEqual(first_point['easting'], 630000)
        self.assertEqual(first_point['northing'], 170000)
        second_point = resp.json[1]
        self.assertEqual(second_point['dist'], 40)
        self.assertEqual(second_point['alts']['COMB'], 568.5)
        self.assertEqual(second_point['easting'], 630032.0)
        self.assertEqual(second_point['northing'], 170024.0)
        self.__verify_point_is_present(resp, POINT_1_LV03)
        self.__verify_point_is_present(resp, POINT_2_LV03)
        self.__verify_point_is_present(resp, POINT_3_LV03)

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_layers_post(self, mock_get_raster):
        params = {'geom': create_json(4, 21781)}
        content_type, body = self.testapp.encode_multipart(params.iteritems(), [])
        self.headers['Content-Type'] = str(content_type)
        resp = self.__prepare_mock_and_test_post(mock_get_raster, body=body, expected_status=200)
        self.assertEqual(resp.content_type, 'application/json')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_layers_none(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': '{"type":"LineString","coordinates":[[0,0],[0,0],[0,0]]}'},
                                                         expected_status=400)
        resp.mustcontain("No 'sr' given and cannot be guessed from 'geom'")

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_layers_none2(self, mock_get_raster):
        resp = self.__get_json_profile(
            params={'geom': '{"type":"LineString","coordinates":[[550050,-206550],[556950,204150],[561050,207950]]}'},
            expected_status=400)
        resp.mustcontain("No 'sr' given and cannot be guessed from 'geom'")

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_json_with_callback_valid(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': create_json(4, 21781),
                                               'callback': 'cb_'},
                                                         expected_status=200)
        self.assertEqual(resp.content_type, 'application/javascript')
        resp.mustcontain('cb_([')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_json_missing_geom(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params=None, expected_status=400)
        resp.mustcontain('Missing parameter geom')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_json_wrong_geom(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': 'toto'},
                                                         expected_status=400)
        resp.mustcontain('Error loading geometry in JSON string')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_json_wrong_shape(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': LINESTRING_WRONG_SHAPE},
                                                         expected_status=400)
        resp.mustcontain('Error converting JSON to Shape')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_json_nb_points(self, mock_get_raster):
        # as 150 is too much for this profile (distance between points will be smaller than 2m resolution of the
        # altitude model), the service will return 203 and a smaller amount of points
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': LINESTRING_SMALL_LINE_LV03,
                                                                 'smart_filling': True,
                                                                 'nb_points': '150'},
                                                         expected_status=203)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertNotEqual(len(resp.json), 150)

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_json_simplify_linestring(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': create_json(4, 21781),
                                                                 'nb_points': '2'},
                                                         expected_status=200)
        self.assertEqual(resp.content_type, 'application/json')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_json_nbPoints(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': LINESTRING_SMALL_LINE_LV03,
                                                                 'smart_filling': True,
                                                                 'nbPoints': '150'},
                                                         expected_status=203)

        self.assertEqual(resp.content_type, 'application/json')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_json_nb_points_wrong(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': create_json(4, 21781),
                                                                 'nb_points': 'toto'},
                                                         expected_status=400)
        resp.mustcontain("Please provide a numerical value for the parameter 'NbPoints'/'nb_points'")

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_json_nb_points_too_much(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': create_json(4, 21781),
                                                                 'nb_points': PROFILE_MAX_AMOUNT_POINTS + 1},
                                                         expected_status=400)
        resp.mustcontain("Please provide a numerical value for the parameter 'NbPoints'/'nb_points'")

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_json_default_nb_points(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': LINESTRING_VALID_LV03},
                                                         expected_status=200)
        self.assertGreaterEqual(len(resp.json), PROFILE_DEFAULT_AMOUNT_POINTS)
        self.assertLessEqual(len(resp.json), PROFILE_MAX_AMOUNT_POINTS)

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_csv_valid(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_csv_profile(mock_get_raster, params={'geom': create_json(4, 21781)},
                                                        expected_status=200)
        self.assertEqual(resp.content_type, 'text/csv')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_cvs_wrong_geom(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_csv_profile(mock_get_raster, params={'geom': 'toto'},
                                                        expected_status=400)
        resp.mustcontain('Error loading geometry in JSON string')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_csv_misspelled_shape(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_csv_profile(mock_get_raster, params={'geom': LINESTRING_MISSPELLED_SHAPE},
                                                        expected_status=400)
        resp.mustcontain('Error loading geometry in JSON string')

        resp = self.__prepare_mock_and_test_csv_profile(mock_get_raster, params={'geom': LINESTRING_WRONG_SHAPE},
                                                        expected_status=400)
        resp.mustcontain('Error converting JSON to Shape')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_json_invalid_linestring(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': '{"type":"LineString","coordinates":[[550050,206550]]}'},
                                                         expected_status=400)
        resp.mustcontain('Error converting JSON to Shape')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_json_offset(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': LINESTRING_VALID_LV03,
                                                                 'offset': '1'},
                                                         expected_status=200)
        self.assertTrue(resp.content_type == 'application/json')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv03_json_invalid_offset(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': LINESTRING_VALID_LV03,
                                                                 'offset': 'asdf'},
                                                         expected_status=400)
        resp.mustcontain("Please provide a numerical value for the parameter 'offset'")

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_entity_too_large(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': create_json(7000),
                                                                 'sr': '2056'},
                                                         expected_status=413)
        resp.mustcontain('LineString too large')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_entity_too_large_post(self, mock_get_raster):
        params = {'geom': create_json(7000), 'sr': '2056'}
        content_type, body = self.testapp.encode_multipart(params.iteritems(), [])
        self.headers['Content-Type'] = str(content_type)
        resp = self.__prepare_mock_and_test_post(mock_get_raster, body=body, expected_status=413)
        resp.mustcontain('LineString too large')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv95(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': LINESTRING_VALID_LV95},
                                                         expected_status=200)
        self.assertTrue(resp.content_type == 'application/json')

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_lv95_nb_points_exceeds_resolution_meshing(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': LINESTRING_SMALL_LINE_LV95,
                                                                 'smart_filling': True,
                                                                 'nb_points': 150},
                                                         expected_status=203)
        self.assertTrue(resp.content_type == 'application/json')
        self.assertNotEqual(len(resp.json), 150)

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_points_given_in_geom_are_in_profile(self, mock_get_raster):
        point1, point2, point3, point4, point5, point6, point7 = [2631599.9, 1171895.0], [2631960.5, 1171939.7], \
                                                                 [2632384.3, 1171798.3], [2632600.9, 1171525.6], \
                                                                 [2632633.5, 1171204.0], [2632622.1, 1171025.3], \
                                                                 [2632820.8, 1170741.8]
        multipoint_geom = '{\"type\":\"LineString\",\"coordinates\":[' \
                          + str(point1) + ',' \
                          + str(point2) + ',' \
                          + str(point3) + ',' \
                          + str(point4) + ',' \
                          + str(point5) + ',' \
                          + str(point6) + ',' \
                          + str(point7) \
                          + ']}'
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': multipoint_geom},
                                                         expected_status=200)
        self.__verify_point_is_present(resp, point1, msg="point1 not present")
        self.__verify_point_is_present(resp, point2, msg="point2 not present")
        self.__verify_point_is_present(resp, point3, msg="point3 not present")
        self.__verify_point_is_present(resp, point4, msg="point4 not present")
        self.__verify_point_is_present(resp, point5, msg="point5 not present")
        self.__verify_point_is_present(resp, point6, msg="point6 not present")
        self.__verify_point_is_present(resp, point7, msg="point7 not present")

    @patch('alti.lib.profile_helpers.get_raster')
    def test_profile_all_old_elevation_models_are_returned(self, mock_get_raster):
        resp = self.__prepare_mock_and_test_json_profile(mock_get_raster, params={'geom': LINESTRING_VALID_LV95},
                                                         expected_status=200)
        self.assertTrue(resp.content_type == 'application/json')
        altitudes = resp.json[0]['alts']
        comb_value = altitudes['COMB']
        self.assertIsNotNone(altitudes.get('DTM2'),
                             msg="All old elevation_models must be returned in alt for compatibility issue")
        self.assertEqual(altitudes['DTM2'], comb_value,
                         msg="All values from all models should be taken from the new COMB layer")
        self.assertIsNotNone(altitudes.get('DTM25'),
                             msg="All old elevation_models must be returned in alt for compatibility issue")
        self.assertEqual(altitudes['DTM25'], comb_value,
                         msg="All values from all models should be taken from the new COMB layer")
