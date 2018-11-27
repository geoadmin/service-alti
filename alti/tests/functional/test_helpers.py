# -*- coding: utf-8 -*-

import unittest
from shapely.geometry import Point
from alti.lib.helpers import float_raise_nan, filter_alt
from alti.lib.validation import srs_guesser


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
        self.assertEqual(srs_guesser(Point(7, 46)), 4326)
        self.assertEqual(srs_guesser(Point(600000, 200000)), 21781)
        self.assertEqual(srs_guesser(Point(2600000, 1200000)), 2056)
        self.assertEqual(srs_guesser(Point(800000, 5900000)), 3857)
        self.assertEqual(srs_guesser(Point(2, 2)), None)
