import unittest
from mock import patch
from alti.lib.height_helpers import get_height

FAKE_VALUE = 1234.5


def prepare_mock(mock_get_raster, return_value):
    mock_get_raster.return_value.get_height_for_coordinate.return_value = return_value


class TestHeight(unittest.TestCase):

    def __prepare_mock_and_test(self, mock,
                                spatial_reference=2056,
                                northing=12345.6,
                                easting=12345.6,
                                return_value=FAKE_VALUE):
        prepare_mock(mock, return_value=return_value)
        response = get_height(spatial_reference=spatial_reference,
                              northing=northing,
                              easting=easting)
        self.assertIsNotNone(response)
        return response

    @patch('alti.lib.height_helpers.get_raster')
    def test_simple_request(self, mock_get_raster):
        response = self.__prepare_mock_and_test(mock_get_raster)
        self.assertIsNotNone(response)
        self.assertEqual(response, FAKE_VALUE)

    @patch('alti.lib.height_helpers.get_raster')
    def test_rounding(self, mock_get_raster):
        response = self.__prepare_mock_and_test(mock_get_raster, return_value=1.23456789)
        self.assertIsNotNone(response)
        self.assertEqual(response, 1.2)
