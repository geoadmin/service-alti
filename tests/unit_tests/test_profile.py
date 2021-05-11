# -*- coding: utf-8 -*-
import unittest
import json
import logging

from mock import patch

with patch('os.path.exists') as mock_exists:
    mock_exists.return_value = True
    import app as service_alti

from tests import create_json
from tests.unit_tests import ENDPOINT_FOR_JSON_PROFILE, ENDPOINT_FOR_CSV_PROFILE,\
    LINESTRING_VALID_LV03, POINT_1_LV03, POINT_2_LV03, POINT_3_LV03, LINESTRING_WRONG_SHAPE,\
    LINESTRING_SMALL_LINE_LV03, LINESTRING_MISSPELLED_SHAPE, LINESTRING_VALID_LV95,\
    LINESTRING_SMALL_LINE_LV95, DEFAULT_HEADERS, prepare_mock
from app.helpers.profile_helpers import PROFILE_MAX_AMOUNT_POINTS, PROFILE_DEFAULT_AMOUNT_POINTS

logger = logging.getLogger(__name__)


class TestProfile(unittest.TestCase):
    # pylint: disable=too-many-public-methods

    def setUp(self) -> None:
        service_alti.app.config['TESTING'] = True
        self.test_instance = service_alti.app.test_client()
        self.headers = DEFAULT_HEADERS

    def __check_response(self, response, expected_status=200):
        self.assertIsNotNone(response)
        self.assertEqual(
            response.status_code, expected_status, msg="%s" % response.get_data(as_text=True)
        )

    def prepare_mock_and_test_post(self, mock_georaster_utils, body, expected_status):
        prepare_mock(mock_georaster_utils)
        response = self.post_with_body(body)
        self.__check_response(response, expected_status)
        return response

    def prepare_mock_and_test_csv_profile(self, mock_georaster_utils, params, expected_status):
        prepare_mock(mock_georaster_utils)
        response = self.get_csv_with_params(params)
        self.__check_response(response, expected_status)
        return response

    # pylint: disable=inconsistent-return-statements
    def get_json_profile(self, params, expected_status=200):
        # pylint: disable=broad-except
        try:
            response = self.test_instance.get(
                ENDPOINT_FOR_JSON_PROFILE, query_string=params, headers=self.headers
            )
            self.__check_response(response, expected_status)
            return response
        except Exception as e:
            logger.exception(e)
            self.fail('Call to test_instance failed: %s' % (e))

    def get_csv_with_params(self, params):
        return self.test_instance.get(
            ENDPOINT_FOR_CSV_PROFILE, query_string=params, headers=self.headers
        )

    def post_with_body(self, body):
        return self.test_instance.post(ENDPOINT_FOR_JSON_PROFILE, data=body, headers=self.headers)

    def prepare_mock_and_test_json_profile(self, mock_georaster_utils, params, expected_status):
        prepare_mock(mock_georaster_utils)
        return self.get_json_profile(params=params, expected_status=expected_status)

    def verify_point_is_present(self, response, point, msg="point not present"):
        self.assertEqual(response.content_type, "application/json")
        if len(point) != 2:
            self.fail("Point must be a [x,y] point")
        present = False
        for profile_point in response.json:
            if point[0] == profile_point['easting'] and point[1] == profile_point['northing']:
                present = True
        if not present:
            self.fail(msg)

    def assert_response_contains(self, response, content):
        self.assertTrue(
            content in response.get_data(as_text=True),
            msg="Response doesn't contain '%s' : '%s'" % (content, response.get_data(as_text=True))
        )

    @patch('app.routes.georaster_utils')
    def test_do_not_fail_when_no_origin(self, mock_georaster_utils):
        self.headers = {}
        self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'sr': 2056, 'geom': create_json(4, 2056)
            },
            expected_status=200
        )

    @patch('app.routes.georaster_utils')
    def test_profile_invalid_sr_json_valid(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'sr': 666, 'geom': create_json(3, 21781)
            },
            expected_status=400
        )
        self.assert_response_contains(
            resp,
            "Please provide a valid number for the spatial reference "
            "system model 21781 or 2056"
        )

    @patch('app.routes.georaster_utils')
    def test_profile_lv95_json_valid(self, mock_georaster_utils):
        self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'sr': 2056, 'geom': create_json(4, 2056)
            },
            expected_status=200
        )

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_valid(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': LINESTRING_VALID_LV03, 'smart_filling': True, 'offset': 0
            },
            expected_status=200
        )
        self.assertEqual(resp.content_type, 'application/json')
        first_point = resp.json[0]
        self.assertEqual(first_point['dist'], 0)
        self.assertEqual(first_point['alts']['COMB'], 104.0)
        self.assertEqual(first_point['easting'], 630000)
        self.assertEqual(first_point['northing'], 170000)
        second_point = resp.json[1]
        self.assertEqual(second_point['dist'], 40)
        self.assertEqual(second_point['alts']['COMB'], 123.5)
        self.assertEqual(second_point['easting'], 630032.0)
        self.assertEqual(second_point['northing'], 170024.0)
        self.verify_point_is_present(resp, POINT_1_LV03)
        self.verify_point_is_present(resp, POINT_2_LV03)
        self.verify_point_is_present(resp, POINT_3_LV03)

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_layers_post(self, mock_georaster_utils):
        params = create_json(4, 21781)
        self.headers['Content-Type'] = 'application/json'
        resp = self.prepare_mock_and_test_post(
            mock_georaster_utils=mock_georaster_utils, body=json.dumps(params), expected_status=200
        )
        self.assertEqual(resp.content_type, 'application/json')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_layers_none(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': '{"type":"LineString","coordinates":[[0,0],[0,0],[0,0]]}'},
            expected_status=400
        )
        self.assert_response_contains(resp, "No 'sr' given and cannot be guessed from 'geom'")

    def test_profile_lv03_layers_none2(self):
        resp = self.get_json_profile(
            params={
                'geom':
                    '{"type":"LineString","coordinates":[[550050,-206550],[556950,204150],'
                    '[561050,207950]]}'
            },
            expected_status=400
        )
        self.assert_response_contains(resp, "No 'sr' given and cannot be guessed from 'geom'")

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_with_callback_valid(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': create_json(4, 21781), 'callback': 'cb_'
            },
            expected_status=200
        )
        self.assertEqual(resp.content_type, 'application/javascript')
        self.assert_response_contains(resp, 'cb_([')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_missing_geom(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'sr': 21781, 'geom': None
            },
            expected_status=400
        )
        self.assert_response_contains(resp, 'No \'geom\' given')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_wrong_geom(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils, params={'geom': 'toto'}, expected_status=400
        )
        self.assert_response_contains(resp, 'Error loading geometry in JSON string')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_wrong_shape(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': LINESTRING_WRONG_SHAPE},
            expected_status=400
        )
        self.assert_response_contains(resp, 'Error converting JSON to Shape')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_nb_points(self, mock_georaster_utils):
        # as 150 is too much for this profile (distance between points will be smaller than 2m
        # resolution of the altitude model), the service will return 203 and a smaller amount of
        # points
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': LINESTRING_SMALL_LINE_LV03, 'smart_filling': True, 'nb_points': '150'
            },
            expected_status=203
        )
        self.assertEqual(resp.content_type, 'application/json')
        self.assertNotEqual(len(resp.json), 150)

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_simplify_linestring(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': create_json(4, 21781), 'nb_points': '2'
            },
            expected_status=200
        )
        self.assertEqual(resp.content_type, 'application/json')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_nb_points_smart_filling(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': LINESTRING_SMALL_LINE_LV03, 'smart_filling': True, 'nbPoints': '150'
            },
            expected_status=203
        )
        self.assertEqual(resp.content_type, 'application/json')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_nb_points_wrong(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': create_json(4, 21781), 'nb_points': 'toto'
            },
            expected_status=400
        )
        self.assert_response_contains(
            resp, "Please provide a numerical value for the parameter "
            "'NbPoints'/'nb_points'"
        )

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_nb_points_too_much(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': create_json(4, 21781), 'nb_points': PROFILE_MAX_AMOUNT_POINTS + 1
            },
            expected_status=400
        )
        self.assert_response_contains(
            resp, "Please provide a numerical value for the parameter "
            "'NbPoints'/'nb_points'"
        )

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_default_nb_points(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': LINESTRING_VALID_LV03},
            expected_status=200
        )
        self.assertGreaterEqual(len(resp.json), PROFILE_DEFAULT_AMOUNT_POINTS)
        self.assertGreaterEqual(PROFILE_MAX_AMOUNT_POINTS, len(resp.json))

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_csv_valid(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_csv_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': create_json(4, 21781)},
            expected_status=200
        )
        self.assertEqual(resp.content_type, 'text/csv')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_cvs_wrong_geom(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_csv_profile(
            mock_georaster_utils=mock_georaster_utils, params={'geom': 'toto'}, expected_status=400
        )
        self.assert_response_contains(resp, 'Error loading geometry in JSON string')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_csv_misspelled_shape(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_csv_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': LINESTRING_MISSPELLED_SHAPE},
            expected_status=400
        )
        self.assert_response_contains(resp, 'Error loading geometry in JSON string')

        resp = self.prepare_mock_and_test_csv_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': LINESTRING_WRONG_SHAPE},
            expected_status=400
        )
        self.assert_response_contains(resp, 'Error converting JSON to Shape')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_invalid_linestring(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': '{"type":"LineString","coordinates":[[550050,206550]]}'},
            expected_status=400
        )
        self.assert_response_contains(resp, 'Error converting JSON to Shape')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_offset(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': LINESTRING_VALID_LV03, 'offset': '1'
            },
            expected_status=200
        )
        self.assertEqual(resp.content_type, 'application/json')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_invalid_offset(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': LINESTRING_VALID_LV03, 'offset': 'asdf'
            },
            expected_status=400
        )
        self.assert_response_contains(
            resp, "Please provide a numerical value for the parameter 'offset'"
        )

    @patch('app.routes.georaster_utils')
    def test_profile_entity_too_large(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': create_json(7000), 'sr': '2056'
            },
            expected_status=413
        )
        self.assert_response_contains(resp, 'Geometry contains too many points')

    @patch('app.routes.georaster_utils')
    def test_profile_entity_too_large_post(self, mock_georaster_utils):
        params = create_json(7000)
        self.headers['Content-Type'] = 'application/json'
        resp = self.prepare_mock_and_test_post(
            mock_georaster_utils=mock_georaster_utils, body=json.dumps(params), expected_status=413
        )
        self.assert_response_contains(resp, 'Geometry contains too many points')

    @patch('app.routes.georaster_utils')
    def test_profile_lv95(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': LINESTRING_VALID_LV95},
            expected_status=200
        )
        self.assertEqual(resp.content_type, 'application/json')

    @patch('app.routes.georaster_utils')
    def test_profile_lv95_nb_points_exceeds_resolution_meshing(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': LINESTRING_SMALL_LINE_LV95, 'smart_filling': True, 'nb_points': 150
            },
            expected_status=203
        )
        self.assertEqual(resp.content_type, 'application/json')
        self.assertNotEqual(len(resp.json), 150)

    @patch('app.routes.georaster_utils')
    def test_profile_points_given_in_geom_are_in_profile(self, mock_georaster_utils):
        point1, point2, point3, point4, point5, point6, point7 = [2631599.9, 1171895.0], \
                                                                 [2631960.5, 1171939.7], \
                                                                 [2632384.3, 1171798.3], \
                                                                 [2632600.9, 1171525.6], \
                                                                 [2632633.5, 1171204.0], \
                                                                 [2632622.1, 1171025.3], \
                                                                 [2632820.8, 1170741.8]
        multipoint_geom = f'{{"type":"LineString","coordinates":[{point1},{point2},{point3},' \
                          f'{point4},{point5},{point6},{point7}]}}'
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': multipoint_geom},
            expected_status=200
        )
        self.verify_point_is_present(resp, point1, msg="point1 not present")
        self.verify_point_is_present(resp, point2, msg="point2 not present")
        self.verify_point_is_present(resp, point3, msg="point3 not present")
        self.verify_point_is_present(resp, point4, msg="point4 not present")
        self.verify_point_is_present(resp, point5, msg="point5 not present")
        self.verify_point_is_present(resp, point6, msg="point6 not present")
        self.verify_point_is_present(resp, point7, msg="point7 not present")

    @patch('app.routes.georaster_utils')
    def test_profile_all_old_elevation_models_are_returned(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_json_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': LINESTRING_VALID_LV95},
            expected_status=200
        )
        self.assertEqual(resp.content_type, 'application/json')
        altitudes = resp.json[0]['alts']
        comb_value = altitudes['COMB']

        if not altitudes.get('DTM2'):
            self.fail("All old elevation_models must be returned in alt for compatibility issue")
        if altitudes['DTM2'] != comb_value:
            self.fail("All values from all models should be taken from the new COMB layer")
        if not altitudes.get('DTM25'):
            self.fail("All old elevation_models must be returned in alt for compatibility issue")
        if altitudes['DTM25'] != comb_value:
            self.fail("All values from all models should be taken from the new COMB layer")
