# -*- coding: utf-8 -*-

from pyramid.events import subscriber, NewRequest
from pyramid.httpexceptions import HTTPRequestEntityTooLarge


@subscriber(NewRequest)
def validate_body_length(event):
    max_clength = 160000
    content_length = event.request.headers.get('Content-Length')
    content_length = content_length or len(event.request.params.get('geom', ''))
    if content_length and int(content_length) > max_clength:
        raise HTTPRequestEntityTooLarge(
            'LineString too large, maximum Content-Length ' +
            'of %s exceeded' % max_clength
        )
