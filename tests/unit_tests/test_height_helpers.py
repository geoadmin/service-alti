import unittest

from mock import Mock
from mock import patch

from app.helpers.height_helpers import get_height

FAKE_VALUE = 1234.5


def prepare_mock(mock_get_raster, return_value):
    fake_tile = Mock()
    fake_tile.get_height_for_coordinate.return_value = return_value
    mock_get_raster.get_raster.return_value = fake_tile


class TestHeightHelpers(unittest.TestCase):

    def __prepare_mock_and_test(
        self,
        mock,
        spatial_reference=2056,
        northing=12345.6,
        easting=12345.6,
        return_value=FAKE_VALUE
    ):
        prepare_mock(mock, return_value=return_value)
        response = get_height(
            spatial_reference=spatial_reference,
            northing=northing,
            easting=easting,
            georaster_utils=mock
        )
        self.assertIsNotNone(response)
        return response

    @patch('app.routes.georaster_utils')
    def test_simple_request(self, mock_get_raster):
        response = self.__prepare_mock_and_test(mock_get_raster)
        self.assertEqual(response, FAKE_VALUE)

    @patch('app.routes.georaster_utils')
    def test_rounding(self, mock_get_raster):
        response = self.__prepare_mock_and_test(mock_get_raster, return_value=1.23456789)
        self.assertEqual(response, 1.2)
