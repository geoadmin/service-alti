import unittest

from mock import patch

with patch('os.path.exists') as mock_exists:
    mock_exists.return_value = True
    import app as service_alti

from flask.helpers import url_for

from tests.unit_tests import DEFAULT_EXTERN_HEADERS
from tests.unit_tests import DEFAULT_HEADERS
from tests.unit_tests import DEFAULT_INTERN_HEADERS


class BaseRouteTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.test_instance = service_alti.app.test_client()
        self.context = service_alti.app.test_request_context()
        self.context.push()
        service_alti.app.config['TESTING'] = True
        self.headers = DEFAULT_HEADERS

    def check_response(self, response, expected_status=200, expected_allowed_methods=None):
        if expected_allowed_methods is None:
            expected_allowed_methods = ['GET', 'HEAD', 'OPTIONS']
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, expected_status, msg=response.get_data(as_text=True))
        self.assertCors(response, expected_allowed_methods)

    def assertCors(self, response, expected_allowed_methods):  # pylint: disable=invalid-name
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')
        self.assertIn('Access-Control-Allow-Methods', response.headers)
        self.assertListEqual(
            sorted(expected_allowed_methods),
            sorted(
                map(
                    lambda m: m.strip(),
                    response.headers['Access-Control-Allow-Methods'].split(',')
                )
            )
        )
        self.assertIn('Access-Control-Allow-Headers', response.headers)
        self.assertEqual(response.headers['Access-Control-Allow-Headers'], '*')


class CheckerTests(BaseRouteTestCase):

    def test_checker_intern_origin(self):
        response = self.test_instance.get(url_for('check'), headers=DEFAULT_INTERN_HEADERS)
        self.check_response(response)
        self.assertNotIn('Cache-Control', response.headers)
        self.assertEqual(response.content_type, "application/json")

    def test_checker_extern_origin(self):
        response = self.test_instance.get(url_for('check'), headers=DEFAULT_EXTERN_HEADERS)
        self.check_response(response)
        self.assertNotIn('Cache-Control', response.headers)
        self.assertEqual(response.content_type, "application/json")
