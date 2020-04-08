# -*- coding: utf-8 -*-

import unittest
from alti.lib.validation.profile import ProfileValidation
from alti.views.profile import PROFILE_DEFAULT_AMOUNT_POINTS, PROFILE_MAX_AMOUNT_POINTS
from alti.tests.integration.test_profile import create_json
from pyramid.httpexceptions import HTTPBadRequest, HTTPRequestEntityTooLarge
import logging
logger = logging.getLogger('alti')

INVALID_LINESTRING_NOT_GEOJSON = "hello world"
VALID_SPATIAL_REFERNECES = [21781, 2056]
INVALID_SPATIAL_REFERENCE = 66600
VALID_OFFSET = "5"
VALID_NB_POINTS = "100"
INVALID_OFFSET = "hello world"


def create_profile_validation(linestring, spatial_reference, nb_points, offset):
    profile_validation = ProfileValidation()
    profile_validation.nb_points_max = PROFILE_MAX_AMOUNT_POINTS
    profile_validation.nb_points_default = PROFILE_DEFAULT_AMOUNT_POINTS
    profile_validation.linestring = linestring
    profile_validation.spatial_reference = spatial_reference
    profile_validation.nb_points = nb_points
    profile_validation.offset = offset
    return profile_validation


class TestProfileValidation(unittest.TestCase):

    def test_profile_validation_valid(self):
        try:
            for srid in VALID_SPATIAL_REFERNECES:
                profile = create_profile_validation(create_json(2, srid), srid, VALID_NB_POINTS, VALID_OFFSET)
                self.assertEquals(srid, profile.spatial_reference)
                self.assertEquals(100, profile.nb_points)
                self.assertEquals(VALID_OFFSET, profile.offset)
        except Exception as e:
            logger.error(e, exc_info=True)
            self.fail("These profiles should be valid")

    def test_profile_validation_valid_nb_points_none(self):
        try:
            profile = create_profile_validation(create_json(2), VALID_SPATIAL_REFERNECES[0], None, VALID_OFFSET)
            self.assertEquals(PROFILE_DEFAULT_AMOUNT_POINTS, profile.nb_points)
        except Exception as e:
            logger.error(e, exc_info=True)
            self.fail("These profiles should be valid, and nb points should be equal to {}".format(PROFILE_DEFAULT_AMOUNT_POINTS))

    def test_profile_validation_valid_offset_none(self):
        try:
            profile = create_profile_validation(create_json(2), VALID_SPATIAL_REFERNECES[0], VALID_NB_POINTS, None)
            self.assertEquals(3, profile.offset)
        except Exception as e:
            logger.error(e, exc_info=True)
            self.fail("These profiles should be valid, and offset should be equal to 3")

    def test_profile_validation_no_linestring(self):
        try:
            create_profile_validation(None, VALID_SPATIAL_REFERNECES[0], VALID_NB_POINTS, VALID_OFFSET)
            self.fail("This should not validate")
        except HTTPBadRequest:
            pass
        except Exception as e:
            logger.error(e, exc_info=True)
            self.fail("We should have an http bad request exception, something else went wrong.")

    def test_profile_validation_not_a_geojson_linestring(self):
        try:
            create_profile_validation(INVALID_LINESTRING_NOT_GEOJSON, VALID_SPATIAL_REFERNECES[0], VALID_NB_POINTS, VALID_OFFSET)
            self.fail("This should not validate")
        except HTTPBadRequest:
            pass
        except Exception as e:
            logger.error(e, exc_info=True)
            self.fail("We should have an http bad request exception, something else went wrong.")

    def test_profile_validation_linestring_too_long(self):
        try:
            create_profile_validation(create_json(PROFILE_MAX_AMOUNT_POINTS + 210), VALID_SPATIAL_REFERNECES[0], VALID_NB_POINTS, VALID_OFFSET)
        except HTTPRequestEntityTooLarge:
            pass
        except Exception as e:
            logger.error(e, exc_info=True)
            self.fail("We should have an http request entity too long exception, something else went wrong.")

    def test_profile_validation_wrong_srid(self):
        try:
            create_profile_validation(create_json(2), INVALID_SPATIAL_REFERENCE, VALID_NB_POINTS, VALID_OFFSET)
            self.fail("This should not validate")
        except HTTPBadRequest:
            pass
        except Exception as e:
            logger.error(e, exc_info=True)
            self.fail("We should have an http bad request exception, something else went wrong.")

    def test_profile_validation_nb_points_less_than_two(self):
        try:
            create_profile_validation(create_json(2), VALID_SPATIAL_REFERNECES[0], "1", VALID_OFFSET)
            self.fail("Should not validate")
        except HTTPBadRequest:
            pass
        except Exception as e:
            logger.error(e, exc_info=True)
            self.fail("We should have an http bad request exception, something else went wrong.")

    def test_profile_validation_nb_points_too_big(self):
        try:
            create_profile_validation(create_json(2), VALID_SPATIAL_REFERNECES[0], str(PROFILE_MAX_AMOUNT_POINTS + 710), VALID_OFFSET)
            self.fail("Should not validate")
        except HTTPBadRequest:
            pass
        except Exception as e:
            logger.error(e, exc_info=True)
            self.fail("We should have an http bad request exception, something else went wrong.")

    def test_profile_validation_nb_points_not_int(self):
        try:
            create_profile_validation(create_json(2), VALID_SPATIAL_REFERNECES[0], "hello world", VALID_OFFSET)
            self.fail("Should not validate")
        except HTTPBadRequest:
            pass
        except Exception as e:
            logger.error(e, exc_info=True)
            self.fail("We should have an http bad request exception, something else went wrong.")

    def test_profile_validation_offset_not_int(self):
        try:
            create_profile_validation(create_json(2), VALID_SPATIAL_REFERNECES[0], VALID_NB_POINTS, INVALID_OFFSET)
            self.fail("Should not validate")
        except HTTPBadRequest:
            pass
        except Exception as e:
            logger.error(e, exc_info=True)
            self.fail("We should have an http bad request exception, something else went wrong.")
