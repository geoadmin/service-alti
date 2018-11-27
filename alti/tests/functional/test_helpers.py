# -*- coding: utf-8 -*-

import unittest
import pyproj
from shapely.geometry import Point, box
from alti.lib.helpers import float_raise_nan, filter_alt, get_proj_from_srid, transform_coordinate, transform_shape
from alti.lib.validation import SrsValidation


class Test_Helpers(unittest.TestCase):

    def test_float_raise_nan(self):
        testval = 5
        result = float_raise_nan(testval)
        self.assertEqual(result, 5.0)
        with self.assertRaises(ValueError):
            float_raise_nan(float('nan'))

    def test_filter_alt(self):
        alt = 100.0
        self.assertEqual(alt, filter_alt(alt))
        alt = -100.0
        self.assertEqual(None, filter_alt(alt))
        alt = None
        self.assertEqual(alt, filter_alt(alt))
        alt = 100.111
        self.assertEqual(100.1, filter_alt(alt))

    def test_srs_guesser(self):
        validator = SrsValidation()
        self.assertEqual(validator.srs_guesser(Point(7, 46)), 4326)
        self.assertEqual(validator.srs_guesser(Point(600000, 200000)), 21781)
        self.assertEqual(validator.srs_guesser(Point(2600000, 1200000)), 2056)
        self.assertEqual(validator.srs_guesser(Point(800000, 5900000)), 3857)
        self.assertEqual(validator.srs_guesser(Point(2, 2)), None)

    def test_get_proj(self):
        self.assertIsInstance(get_proj_from_srid(21781), pyproj.Proj)

    def test_transform_coordinate(self):
        lv03 = (600000, 200000)
        lv95 = transform_coordinate(lv03, 21781, 2056)
        wgs84 = transform_coordinate(lv03, 21781, 4326)
        self.assertLess(abs(lv95[0] - 2600000.0), 0.1)
        self.assertLess(abs(lv95[1] - 1200000.0), 0.1)
        self.assertLess(abs(wgs84[0] - 7.438632495), 0.000001)
        self.assertLess(abs(wgs84[1] - 46.951082877), 0.000001)

    def test_transform_shape(self):
        coords = (2450000, 1030000, 2900000, 1350000)
        box_lv95 = box(*coords)
        bounds_merc = transform_shape(box_lv95, 2056, 3857).bounds
        self.assertLess(abs(bounds_merc[0] - 603111.39), 0.1)
        self.assertLess(abs(bounds_merc[1] - 5677741.73), 0.1)
        self.assertLess(abs(bounds_merc[2] - 1277662.42), 0.1)
        self.assertLess(abs(bounds_merc[3] - 6154011.09), 0.1)

    def test_no_transform_shape(self):
        coords = (2450000, 1030000, 2900000, 1350000)
        box_lv95 = box(*coords)
        bounds  = transform_shape(box_lv95, 2056, 2056).bounds
        self.assertLess(abs(bounds[0] - 2450000.0), 0.0000001)
