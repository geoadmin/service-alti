# -*- coding: utf-8 -*-

from pyramid.events import subscriber, NewRequest
from pyramid.httpexceptions import HTTPBadRequest, HTTPRequestEntityTooLarge


@subscriber(NewRequest)
def validate_body_length(event):
    content_length = 0
    max_clength = 160000
    if event.request.method == 'POST':
        content_length = event.request.headers.get('Content-Length')
        if not content_length:
            raise HTTPBadRequest('No Content-Length was provided in request header')  # pragam: no cover
    elif event.request.method == 'GET':
        content_length = len(event.request.params.get('geom', ''))

    if int(content_length) > max_clength:
        raise HTTPRequestEntityTooLarge(
            'LineString too large, maximum Content-Length ' +
            'of %s exceeded' % max_clength
        )
