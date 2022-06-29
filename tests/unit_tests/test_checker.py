from flask.helpers import url_for

from tests.unit_tests import DEFAULT_EXTERN_HEADERS
from tests.unit_tests import DEFAULT_INTERN_HEADERS
from tests.unit_tests.base import BaseRouteTestCase


class CheckerTests(BaseRouteTestCase):

    def __checker_test_get_request(self, headers):
        response = self.test_instance.get(url_for('check'), headers=headers)
        self.check_response(response)
        self.assertNotIn('Cache-Control', response.headers)
        self.assertEqual(response.content_type, "application/json")

    def test_checker_intern_origin(self):
        self.__checker_test_get_request(DEFAULT_INTERN_HEADERS)

    def test_checker_extern_origin(self):
        self.__checker_test_get_request(DEFAULT_EXTERN_HEADERS)
