ALLOWED_DOMAINS = [
    r'.*\.geo\.admin\.ch',
    r'.*bgdi\.ch',
    r'.*\.swisstopo\.cloud',
]

ALLOWED_DOMAINS_PATTERN = '({})'.format('|'.join(ALLOWED_DOMAINS))
