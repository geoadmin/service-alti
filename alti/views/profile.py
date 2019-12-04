# -*- coding: utf-8 -*-

from pyramid.view import view_config

import cProfile

from alti.lib.profile_helpers import get_profile, PROFILE_MAX_AMOUNT_POINTS, PROFILE_DEFAULT_AMOUNT_POINTS
from alti.lib.validation.profile import ProfileValidation
from alti.lib.validation import srs_guesser

from pyramid.httpexceptions import HTTPBadRequest


class Profile(ProfileValidation):

    def __init__(self, request):
        super(Profile, self).__init__()
        self.nb_points_max = int(request.registry.settings.get('profile_nb_points_maximum',
                                                               PROFILE_MAX_AMOUNT_POINTS))
        self.nb_points_default = int(request.registry.settings.get('profile_nb_points_default',
                                                                   PROFILE_DEFAULT_AMOUNT_POINTS))

        # param geom, list of coordinates defining the line on which we want a profile
        if 'geom' in request.params:
            self.linestring = request.params.get('geom')
        elif request.body is not None:
            self.linestring = request.body
        else:
            self.linestring = request.body
        if not self.linestring:
            raise HTTPBadRequest("No 'geom' given, cannot create a profile without coordinates")

        # param layers (or elevations_models), define on which elevation model the profile has to be made.
        # Possible values are DTM25, DTM2 and COMB (have a look at georaster.py for more info on this)
        # default value is COMB
        if 'layers' in request.params:
            self.layers = request.params.get('layers')
        elif 'elevation_models' in request.params:
            self.layers = request.params.get('elevation_models')
        else:
            self.layers = 'COMB'

        # number of points wanted in the final profile.
        if 'nbPoints' in request.params:
            self.nb_points = request.params.get('nbPoints')
            self.is_custom_nb_points = True
        elif 'nb_points' in request.params:
            self.nb_points = request.params.get('nb_points')
            self.is_custom_nb_points = True
        else:
            self.nb_points = self.nb_points_default
            self.is_custom_nb_points = False

        # param sr (or projection, sr meaning spatial reference), which Swiss projection to use.
        # Possible values are expressed in int, so value for EPSG:2056 (LV95) is 2056
        # and value for EPSG:21781 (LV03) is 21781
        # if this param is not present, it will be guessed from the coordinates present in the param geom
        if 'sr' in request.params:
            self.spatial_reference = int(request.params.get('sr'))
        elif 'projection' in request.params:
            self.spatial_reference = int(request.params.get('projection'))
        else:
            sr = srs_guesser(self.linestring)
            if sr is None:
                raise HTTPBadRequest("No 'sr' given and cannot be guessed from 'geom'")
            self.spatial_reference = sr

        # param offset, used for smoothing. define how many coordinates should be included
        # in the window used for smoothing. If not defined (or value is zero) smoothing is disabled.
        if 'offset' in request.params:
            self.offset = request.params.get('offset')

        # param only_requested_points, which is flag that when set to True will make
        # the profile with only the given points in geom (no filling points)
        if 'only_requested_points' in request.params:
            self.only_requested_points = bool(request.params.get('only_requested_points'))
        else:
            self.only_requested_points = False

        if 'debug_profile' in request.params:
            self.debug_profile = bool(request.params.get('debug_profile'))
        else:
            self.debug_profile = False

        # keeping the request for later use
        self.request = request

    @view_config(route_name='profile_json', renderer='jsonp', http_cache=0)
    def json(self):
        if self.debug_profile:
            profile = cProfile.Profile()
            try:
                profile.enable()
                result = self.__get_profile_from_helper(True)
                profile.disable()
                return result
            finally:
                profile.dump_stats("/var/tmp/service_alti_profile.prof")
        else:
            return self.__get_profile_from_helper(True)

    @view_config(route_name='profile_csv', renderer='csv', http_cache=0)
    def csv(self):
        return self.__get_profile_from_helper(False)

    def __get_profile_from_helper(self, output_to_json=True):
        profile = get_profile(geom=self.linestring,
                              spatial_reference=self.spatial_reference,
                              layers=self.layers,
                              nb_points=self.nb_points,
                              offset=self.offset,
                              only_requested_points=self.only_requested_points,
                              output_to_json=output_to_json)
        # If profile calculation resulted in a lower number of point than requested (because there's no need to add
        # points closer to each other than the min resolution of 2m), we return HTTP 203 to notify that nb_points
        # couldn't be match.
        # Same thing if the user gave a specific resolution to use, but that resulted in too much point and thus the
        # resolution had to be lowered.
        if self.is_custom_nb_points and len(profile) < self.nb_points:
            self.request.response.status = 203
        return profile
