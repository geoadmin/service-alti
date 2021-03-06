import re
from urllib.parse import urlparse

from flask import abort
from flask import current_app as capp

from app.helpers import make_error_msg

ALLOWED_DOMAINS = [
    r'.*\.geo\.admin\.ch',
    r'.*bgdi\.ch',
    r'.*\.swisstopo\.cloud',
]

ALLOWED_DOMAINS_PATTERN = '({})'.format('|'.join(ALLOWED_DOMAINS))


def validate_url(url):
    """Simple URL validation

    If the URL can be parsed and have a valid hostname/domain then the URL is returned otherwise it
    raises a HTTPException(400). See :attr:`ALLOWED_DOMAIN` for valid domain.

    Args:
        url: URL string to validate

    Returns:
        The validated url string

    Raises:
        HTTPException(400) if the URL is not valid
    """
    try:
        result = urlparse(url)
    except ValueError as err:
        capp.logger.error('Invalid URL: %s', str(err))
        abort(make_error_msg(400, f'Invalid URL, {err}'))

    if result.hostname is None:
        capp.logger.error('Invalid URL, could not determine the hostname, url=%s', url)
        abort(make_error_msg(400, 'Invalid URL, could not determine the hostname'))

    if not re.match(ALLOWED_DOMAINS_PATTERN, result.hostname):
        capp.logger.error('URL domain not allowed')
        abort(make_error_msg(400, 'URL domain not allowed'))

    return url
