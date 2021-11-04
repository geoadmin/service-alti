# -*- coding: utf-8 -*-
import logging
import unittest

from mock import patch

with patch('os.path.exists') as mock_exists:
    mock_exists.return_value = True
    import app as service_alti

from app.helpers.profile_helpers import PROFILE_DEFAULT_AMOUNT_POINTS
from app.helpers.profile_helpers import PROFILE_MAX_AMOUNT_POINTS
from tests import create_json
from tests.unit_tests import DEFAULT_HEADERS
from tests.unit_tests import prepare_mock

logger = logging.getLogger(__name__)

INVALID_LINESTRING_NOT_GEOJSON = "hello world"
VALID_SPATIAL_REFERENCES = [21781, 2056]
INVALID_SPATIAL_REFERENCE = 66600
VALID_OFFSET = 5
VALID_NB_POINTS = 100
INVALID_OFFSET = "hello world"


class TestProfileValidation(unittest.TestCase):

    def setUp(self) -> None:
        service_alti.app.config['TESTING'] = True
        self.test_instance = service_alti.app.test_client()
        self.headers = DEFAULT_HEADERS

    def assert_response(self, response, expected_status=200):
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, expected_status, msg=response.data)

    def prepare_mock_and_test(
        self, linestring, spatial_reference, nb_points, offset, mock_georaster_utils
    ):
        prepare_mock(mock_georaster_utils)
        return self.test_instance.get(
            '/rest/services/profile.json',
            query_string={
                'geom': linestring,
                'sr': spatial_reference,
                'nb_points': nb_points,
                'offset': offset
            },
            headers=self.headers
        )

    @patch('app.routes.georaster_utils')
    def test_profile_validation_valid(self, mock_georaster_utils):
        for srid in VALID_SPATIAL_REFERENCES:
            response = self.prepare_mock_and_test(
                linestring=create_json(2, srid),
                spatial_reference=srid,
                nb_points=VALID_NB_POINTS,
                offset=VALID_OFFSET,
                mock_georaster_utils=mock_georaster_utils
            )
            self.assert_response(response)
            profile = response.get_json()
            self.assertEqual(VALID_NB_POINTS, len(profile))

    @patch('app.routes.georaster_utils')
    def test_profile_validation_valid_nb_points_none(self, mock_georaster_utils):
        response = self.prepare_mock_and_test(
            linestring=create_json(2),
            spatial_reference=VALID_SPATIAL_REFERENCES[0],
            nb_points=None,
            offset=VALID_OFFSET,
            mock_georaster_utils=mock_georaster_utils
        )
        self.assert_response(response)
        profile = response.get_json()
        self.assertEqual(PROFILE_DEFAULT_AMOUNT_POINTS, len(profile))

    @patch('app.routes.georaster_utils')
    def test_profile_validation_valid_offset_none(self, mock_georaster_utils):
        response = self.prepare_mock_and_test(
            linestring=create_json(2),
            spatial_reference=VALID_SPATIAL_REFERENCES[0],
            nb_points=VALID_NB_POINTS,
            offset=None,
            mock_georaster_utils=mock_georaster_utils
        )
        self.assert_response(response)

    @patch('app.routes.georaster_utils')
    def test_profile_validation_no_linestring(self, mock_georaster_utils):
        response = self.prepare_mock_and_test(
            linestring=None,
            spatial_reference=VALID_SPATIAL_REFERENCES[0],
            nb_points=VALID_NB_POINTS,
            offset=VALID_OFFSET,
            mock_georaster_utils=mock_georaster_utils
        )
        self.assert_response(response, expected_status=400)

    @patch('app.routes.georaster_utils')
    def test_profile_validation_not_a_geojson_linestring(self, mock_georaster_utils):
        response = self.prepare_mock_and_test(
            linestring=INVALID_LINESTRING_NOT_GEOJSON,
            spatial_reference=VALID_SPATIAL_REFERENCES[0],
            nb_points=VALID_NB_POINTS,
            offset=VALID_OFFSET,
            mock_georaster_utils=mock_georaster_utils
        )
        self.assert_response(response, expected_status=400)

    @patch('app.routes.georaster_utils')
    def test_profile_validation_linestring_too_long(self, mock_georaster_utils):
        response = self.prepare_mock_and_test(
            linestring=create_json(PROFILE_MAX_AMOUNT_POINTS + 210),
            spatial_reference=VALID_SPATIAL_REFERENCES[0],
            nb_points=VALID_NB_POINTS,
            offset=VALID_OFFSET,
            mock_georaster_utils=mock_georaster_utils
        )
        self.assert_response(response, expected_status=413)

    @patch('app.routes.georaster_utils')
    def test_profile_validation_wrong_srid(self, mock_georaster_utils):
        response = self.prepare_mock_and_test(
            linestring=create_json(2),
            spatial_reference=INVALID_SPATIAL_REFERENCE,
            nb_points=VALID_NB_POINTS,
            offset=VALID_OFFSET,
            mock_georaster_utils=mock_georaster_utils
        )
        self.assert_response(response, expected_status=400)

    @patch('app.routes.georaster_utils')
    def test_profile_validation_nb_points_less_than_two(self, mock_georaster_utils):
        response = self.prepare_mock_and_test(
            linestring=create_json(2),
            spatial_reference=VALID_SPATIAL_REFERENCES[0],
            nb_points="1",
            offset=VALID_OFFSET,
            mock_georaster_utils=mock_georaster_utils
        )
        self.assert_response(response, expected_status=400)

    @patch('app.routes.georaster_utils')
    def test_profile_validation_nb_points_too_big(self, mock_georaster_utils):
        response = self.prepare_mock_and_test(
            linestring=create_json(2),
            spatial_reference=VALID_SPATIAL_REFERENCES[0],
            nb_points=str(PROFILE_MAX_AMOUNT_POINTS + 710),
            offset=VALID_OFFSET,
            mock_georaster_utils=mock_georaster_utils
        )
        self.assert_response(response, expected_status=400)

    @patch('app.routes.georaster_utils')
    def test_profile_validation_nb_points_not_int(self, mock_georaster_utils):
        response = self.prepare_mock_and_test(
            linestring=create_json(2),
            spatial_reference=VALID_SPATIAL_REFERENCES[0],
            nb_points="hello world",
            offset=VALID_OFFSET,
            mock_georaster_utils=mock_georaster_utils
        )
        self.assert_response(response, expected_status=400)

    @patch('app.routes.georaster_utils')
    def test_profile_validation_offset_not_int(self, mock_georaster_utils):
        response = self.prepare_mock_and_test(
            linestring=create_json(2),
            spatial_reference=VALID_SPATIAL_REFERENCES[0],
            nb_points=VALID_NB_POINTS,
            offset=INVALID_OFFSET,
            mock_georaster_utils=mock_georaster_utils
        )
        self.assert_response(response, expected_status=400)
