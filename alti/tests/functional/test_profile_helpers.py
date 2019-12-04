from unittest import TestCase
from mock import patch, Mock

from shapely.geometry import LineString

from alti.lib.profile_helpers import get_profile

FAKE_GEOM = LineString([(2600000, 1200000), (2600000, 1190000)])


class TestProfileHelpers(TestCase):

    @patch('alti.lib.profile_helpers.get_raster')
    def test_something(self, mock_get_raster):
        georaster_mock = Mock()
        tile_mock = Mock()
        georaster_mock.get_tile.return_value = tile_mock
        tile_mock.get_height_for_coordinate.return_value = 12.34567
        mock_get_raster.return_value = georaster_mock
        response = get_profile(geom=FAKE_GEOM,
                               spatial_reference=2056,
                               layers=['COMB'],
                               nb_points=2,
                               offset=0,
                               only_requested_points=False,
                               output_to_json=True)
        self.assertIsNotNone(response)
        for profile in response:
            self.assertEqual(profile['alts']['COMB'], 12.3)
