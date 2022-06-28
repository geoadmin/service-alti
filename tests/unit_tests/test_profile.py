# -*- coding: utf-8 -*-
import csv
import json
import logging
from io import StringIO

from mock import patch

from app.helpers.profile_helpers import PROFILE_DEFAULT_AMOUNT_POINTS
from app.helpers.profile_helpers import PROFILE_MAX_AMOUNT_POINTS
from tests import create_json
from tests.unit_tests import ENDPOINT_FOR_CSV_PROFILE
from tests.unit_tests import ENDPOINT_FOR_JSON_PROFILE
from tests.unit_tests import LINESTRING_MISSPELLED_SHAPE
from tests.unit_tests import LINESTRING_SMALL_LINE_LV03
from tests.unit_tests import LINESTRING_SMALL_LINE_LV95
from tests.unit_tests import LINESTRING_VALID_LV03
from tests.unit_tests import LINESTRING_VALID_LV95
from tests.unit_tests import LINESTRING_WRONG_SHAPE
from tests.unit_tests import POINT_1_LV03
from tests.unit_tests import POINT_2_LV03
from tests.unit_tests import POINT_3_LV03
from tests.unit_tests import prepare_mock
from tests.unit_tests.base import BaseRouteTestCase

logger = logging.getLogger(__name__)


class TestProfileBase(BaseRouteTestCase):

    def check_response(self, response, expected_status=200, expected_allowed_methods=None):
        if expected_allowed_methods is None:
            expected_allowed_methods = ['GET', 'HEAD', 'POST', 'OPTIONS']
        super().check_response(response, expected_status, expected_allowed_methods)

    def assert_response_contains(self, response, content):
        self.assertTrue(
            content in response.get_data(as_text=True),
            msg=f"Response doesn't contain '{content}' : '{response.get_data(as_text=True)}'"
        )


class TestProfileJson(TestProfileBase):
    # pylint: disable=too-many-public-methods

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

    def prepare_mock_and_test_get(self, mock_georaster_utils, params, expected_status):
        prepare_mock(mock_georaster_utils)
        return self.get_json_profile(params=params, expected_status=expected_status)

    def prepare_mock_and_test_post_json(self, mock_georaster_utils, body, expected_status):
        prepare_mock(mock_georaster_utils)
        response = self.test_instance.post(
            ENDPOINT_FOR_JSON_PROFILE, data=body, headers=self.headers
        )
        self.check_response(response, expected_status)
        return response

    def prepare_mock_and_test_post_urlencoded(
        self, mock_georaster_utils, body, expected_status, query=None, headers=None
    ):
        prepare_mock(mock_georaster_utils)
        response = self.test_instance.post(
            ENDPOINT_FOR_JSON_PROFILE, data=body, query_string=query, headers=None
        )
        self.check_response(response, expected_status)
        return response

    def get_json_profile(self, params, expected_status=200):
        # pylint: disable=broad-except
        try:
            response = self.test_instance.get(
                ENDPOINT_FOR_JSON_PROFILE, query_string=params, headers=self.headers
            )
            self.check_response(response, expected_status)
            return response
        except Exception as e:
            logger.exception(e)
            self.fail(f'Call to test_instance failed: {e}')
        return None

    @patch('app.routes.georaster_utils')
    def test_do_not_fail_when_no_origin(self, mock_georaster_utils):
        self.headers = {}
        self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'sr': 2056, 'geom': create_json(4, 2056)
            },
            expected_status=200
        )

    @patch('app.routes.georaster_utils')
    def test_profile_invalid_sr_json_valid(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'sr': 666, 'geom': create_json(3, 21781)
            },
            expected_status=400
        )
        self.assert_response_contains(
            resp,
            "Please provide a valid number for the spatial reference "
            "system model: 21781, 2056"
        )

    @patch('app.routes.georaster_utils')
    def test_profile_lv95_json_valid(self, mock_georaster_utils):
        self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'sr': 2056, 'geom': create_json(4, 2056)
            },
            expected_status=200
        )

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_valid(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_get(
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
        resp = self.prepare_mock_and_test_post_json(
            mock_georaster_utils=mock_georaster_utils, body=params, expected_status=200
        )
        self.assertEqual(resp.content_type, 'application/json')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_layers_post_content_type_With_charset(self, mock_georaster_utils):
        params = create_json(4, 21781)
        self.headers['Content-Type'] = 'application/json; charset=utf-8'
        resp = self.prepare_mock_and_test_post_json(
            mock_georaster_utils=mock_georaster_utils, body=params, expected_status=200
        )
        self.assertEqual(resp.content_type, 'application/json')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_layers_none(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': '{"type":"LineString","coordinates":[[0,0],[0,0],[0,0]]}'},
            expected_status=400
        )
        self.assert_response_contains(resp, "Invalid LineString")

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
        resp = self.prepare_mock_and_test_get(
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
        resp = self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'sr': 21781, 'geom': None
            },
            expected_status=400
        )
        self.assert_response_contains(resp, 'No \'geom\' given')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_wrong_geom(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils, params={'geom': 'toto'}, expected_status=400
        )
        self.assert_response_contains(resp, 'Invalid geom parameter, must be a GEOJSON')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_wrong_shape(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': LINESTRING_WRONG_SHAPE},
            expected_status=400
        )
        self.assert_response_contains(resp, 'geom parameter must be a LineString/Point GEOJSON')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_small_line(self, mock_georaster_utils):

        resp = self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': LINESTRING_SMALL_LINE_LV03},
            expected_status=200
        )
        self.assertEqual(resp.content_type, 'application/json')
        self.assertLessEqual(len(resp.json), PROFILE_DEFAULT_AMOUNT_POINTS)

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_nb_points_smart_filling(self, mock_georaster_utils):
        # as 150 is too much for this profile (distance between points will be smaller than 2m
        # resolution of the altitude model), the service will return 203 and a smaller amount of
        # points
        resp = self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': LINESTRING_SMALL_LINE_LV03, 'smart_filling': True, 'nb_points': '150'
            },
            expected_status=203
        )
        self.assertEqual(resp.content_type, 'application/json')
        self.assertLessEqual(len(resp.json), 150)

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_fewer_nb_points_as_input_point(self, mock_georaster_utils):
        input_points = 4
        resp = self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': create_json(input_points, 21781), 'nb_points': '2'
            },
            expected_status=203
        )
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(len(resp.json), input_points)

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_only_input_point(self, mock_georaster_utils):
        input_points = 4
        resp = self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': create_json(input_points, 21781), 'only_requested_points': True
            },
            expected_status=200
        )
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(len(resp.json), input_points)

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_nb_points_wrong(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_get(
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
        resp = self.prepare_mock_and_test_get(
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
        resp = self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': LINESTRING_VALID_LV03},
            expected_status=200
        )
        self.assertGreaterEqual(len(resp.json), PROFILE_DEFAULT_AMOUNT_POINTS)
        self.assertGreaterEqual(PROFILE_MAX_AMOUNT_POINTS, len(resp.json))

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_invalid_linestring(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': '{"type":"LineString","coordinates":[[550050,206550]]}'},
            expected_status=400
        )
        self.assert_response_contains(resp, 'Error converting GEOJSON to Shape')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_offset(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': LINESTRING_VALID_LV03, 'offset': '1'
            },
            expected_status=200
        )
        self.assertEqual(resp.content_type, 'application/json')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_json_invalid_offset(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_get(
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
        resp = self.prepare_mock_and_test_get(
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
        resp = self.prepare_mock_and_test_post_json(
            mock_georaster_utils=mock_georaster_utils, body=params, expected_status=413
        )
        self.assert_response_contains(resp, 'Geometry contains too many points')

    @patch('app.routes.georaster_utils')
    def test_profile_lv95(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_get(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': LINESTRING_VALID_LV95},
            expected_status=200
        )
        self.assertEqual(resp.content_type, 'application/json')

    @patch('app.routes.georaster_utils')
    def test_profile_lv95_nb_points_exceeds_resolution_meshing(self, mock_georaster_utils):
        resp = self.prepare_mock_and_test_get(
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
        resp = self.prepare_mock_and_test_get(
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
        resp = self.prepare_mock_and_test_get(
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

    @patch('app.routes.georaster_utils')
    def test_post_profile_url_encoded(self, mock_georaster_utils):

        nb_points = 10
        response = self.prepare_mock_and_test_post_urlencoded(
            mock_georaster_utils,
            {
                'geom': LINESTRING_VALID_LV95, 'nb_points': nb_points
            },
            200,
        )
        self.assertEqual(response.content_type, 'application/json')
        self.assertIsInstance(response.json, list)
        self.assertAlmostEqual(len(response.json), nb_points, delta=1)

    @patch('app.routes.georaster_utils')
    def test_post_profile_url_encoded_and_query(self, mock_georaster_utils):

        nb_points = 10
        response = self.prepare_mock_and_test_post_urlencoded(
            mock_georaster_utils, {'geom': LINESTRING_VALID_LV95},
            200,
            query={'nb_points': nb_points}
        )
        self.assertEqual(response.content_type, 'application/json')
        self.assertIsInstance(response.json, list)
        self.assertAlmostEqual(len(response.json), nb_points, delta=1)

    @patch('app.routes.georaster_utils')
    def test_post_profile_url_encoded_and_query_precedence(self, mock_georaster_utils):
        nb_points = 10
        response = self.prepare_mock_and_test_post_urlencoded(
            mock_georaster_utils, {
                'geom': LINESTRING_VALID_LV95, 'nb_points': nb_points
            },
            200,
            query={'nb_points': 100}
        )
        self.assertEqual(response.content_type, 'application/json')
        self.assertIsInstance(response.json, list)
        self.assertAlmostEqual(len(response.json), nb_points, delta=1)

    @patch('app.routes.georaster_utils')
    def test_post_profile_url_encoded_wrong_sr(self, mock_georaster_utils):

        nb_points = 10
        response = self.prepare_mock_and_test_post_urlencoded(
            mock_georaster_utils,
            {
                'geom': LINESTRING_VALID_LV95, 'nb_points': nb_points, 'sr': 12345
            },
            400,
        )
        self.assertEqual(response.content_type, 'application/json')

    @patch('app.routes.georaster_utils')
    def test_post_profile_url_encoded_wrong_offset(self, mock_georaster_utils):

        nb_points = 10
        response = self.prepare_mock_and_test_post_urlencoded(
            mock_georaster_utils,
            {
                'geom': LINESTRING_VALID_LV95, 'nb_points': nb_points, 'offset': 'bla'
            },
            400,
        )
        self.assertEqual(response.content_type, 'application/json')


class TestProfileCsv(TestProfileBase):

    @classmethod
    def parse_csv(cls, data):
        reader = csv.reader(StringIO(data))
        parsed_data = list(reader)
        return parsed_data

    def mock_get_csv_profile(self, mock_georaster_utils, params, expected_status):
        prepare_mock(mock_georaster_utils)
        response = self.test_instance.get(
            ENDPOINT_FOR_CSV_PROFILE, query_string=params, headers=self.headers
        )
        self.check_response(response, expected_status)
        return response

    def mock_post_json_csv_profile(
        self, mock_georaster_utils, body, expected_status, query=None, headers=None
    ):
        prepare_mock(mock_georaster_utils)
        response = self.test_instance.post(
            ENDPOINT_FOR_CSV_PROFILE, json=body, query_string=query, headers=headers
        )
        self.check_response(response, expected_status)
        return response

    def mock_post_urlencoded_csv_profile(
        self, mock_georaster_utils, body, expected_status, headers=None
    ):
        prepare_mock(mock_georaster_utils)
        response = self.test_instance.post(ENDPOINT_FOR_CSV_PROFILE, data=body, headers=None)
        self.check_response(response, expected_status)
        return response

    def prepare_mock_and_test_post_csv_profile(self, mock_georaster_utils, params, expected_status):
        prepare_mock(mock_georaster_utils)
        response = self.test_instance.post(
            ENDPOINT_FOR_CSV_PROFILE, query_string=params, headers=self.headers
        )
        self.check_response(response, expected_status)
        return response

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_csv_valid(self, mock_georaster_utils):
        resp = self.mock_get_csv_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': create_json(4, 21781)},
            expected_status=200
        )
        self.assertEqual(resp.content_type, 'text/csv')
        data = self.parse_csv(resp.get_data(as_text=True))
        self.assertAlmostEqual(len(data), 200, delta=2)

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_cvs_wrong_geom(self, mock_georaster_utils):
        resp = self.mock_get_csv_profile(
            mock_georaster_utils=mock_georaster_utils, params={'geom': 'toto'}, expected_status=400
        )
        self.assert_response_contains(resp, 'Invalid geom parameter, must be a GEOJSON')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_csv_misspelled_shape(self, mock_georaster_utils):
        resp = self.mock_get_csv_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': LINESTRING_MISSPELLED_SHAPE},
            expected_status=400
        )
        self.assert_response_contains(resp, 'Invalid geom parameter, must be a GEOJSON')

        resp = self.mock_get_csv_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={'geom': LINESTRING_WRONG_SHAPE},
            expected_status=400
        )
        self.assert_response_contains(resp, 'geom parameter must be a LineString/Point GEOJSON')

    @patch('app.routes.georaster_utils')
    def test_profile_lv03_csv_callback(self, mock_georaster_utils):
        resp = self.mock_get_csv_profile(
            mock_georaster_utils=mock_georaster_utils,
            params={
                'geom': create_json(4, 21781), 'callback': '_cb'
            },
            expected_status=400
        )
        self.assert_response_contains(resp, 'callback parameter not supported')

    @patch('app.routes.georaster_utils')
    def test_post_profile_csv_json(self, mock_georaster_utils):
        nb_points = 10
        response = self.mock_post_json_csv_profile(
            mock_georaster_utils,
            json.loads(LINESTRING_VALID_LV95),
            200,
            query={'nb_points': nb_points}
        )
        self.assertEqual(response.content_type, 'text/csv')
        data = self.parse_csv(response.get_data(as_text=True))
        self.assertAlmostEqual(len(data), nb_points, delta=1)

    @patch('app.routes.georaster_utils')
    def test_post_profile_csv_url_encoded(self, mock_georaster_utils):
        nb_points = 10
        response = self.mock_post_urlencoded_csv_profile(
            mock_georaster_utils, {
                'geom': LINESTRING_VALID_LV95, 'nb_points': nb_points
            }, 200
        )
        self.assertEqual(response.content_type, 'text/csv')
        data = self.parse_csv(response.get_data(as_text=True))
        self.assertAlmostEqual(len(data), nb_points, delta=1)
