from unittest import mock

from flask.helpers import url_for

from tests.unit_tests import DEFAULT_EXTERN_HEADERS
from tests.unit_tests import DEFAULT_INTERN_HEADERS
from tests.unit_tests.base import BaseRouteTestCase


class CheckerTests(BaseRouteTestCase):

    def __liveness_test_get_request(self, headers):
        response = self.test_instance.get(url_for('liveness'), headers=headers)
        self.check_response(response)
        self.assertEqual(response.content_type, "application/json")

    def __readiness_test_get_request(self, headers, expected_status=200):
        response = self.test_instance.get(url_for('readiness'), headers=headers)
        self.check_response(response, expected_status=expected_status)
        self.assertEqual(response.content_type, "application/json")

    def test_liveness_intern_origin(self):
        self.__liveness_test_get_request(DEFAULT_INTERN_HEADERS)

    def test_liveness_extern_origin(self):
        self.__liveness_test_get_request(DEFAULT_EXTERN_HEADERS)

    def test_liveness_no_origin(self):
        self.__liveness_test_get_request(None)

    def test_readiness_not_ready(self):
        self.__readiness_test_get_request(None, expected_status=503)

    @mock.patch('app.routes.georaster_utils.raster_files_exists',)
    def test_readiness_no_origin(self, mock_raster_files_exists):
        mock_raster_files_exists.return_value = True
        self.__readiness_test_get_request(None)

    @mock.patch('app.routes.georaster_utils.raster_files_exists',)
    def test_readiness_extern_origin(self, mock_raster_files_exists):
        mock_raster_files_exists.return_value = True
        self.__readiness_test_get_request(DEFAULT_EXTERN_HEADERS)
