# -*- coding: utf-8 -*-

import unittest
from alti.lib.helpers import float_raise_nan, filter_alt


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
