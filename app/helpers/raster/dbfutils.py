# -*- coding: utf-8 -*-

# file taken from http://indiemaps.com/blog/2008/03/easy-shapefile-loading-in-python/

import datetime
import decimal
import itertools
import logging
import struct

logger = logging.getLogger(__name__)


def dbfreader(f):
    # pylint: disable=too-many-locals
    """Returns an iterator over records in a Xbase DBF file.

    The first row returned contains the field names.
    The second row contains field specs: (type, size, decimal places).
    Subsequent rows contain the data records.
    If a record is marked as deleted, it is skipped.

    File should be opened for binary reads.

    """
    # See DBF format spec at:
    #     http://www.pgts.com.au/download/public/xbase.htm#DBF_STRUCT

    numrec, lenheader = struct.unpack('<xxxxLH22x', f.read(32))
    numfields = (lenheader - 33) // 32
    logger.debug('Read dbf: numrec=%d lenheader=%d numfields=%d', numrec, lenheader, numfields)
    fields = []
    for fieldno in range(numfields):
        name, typ, size, deci = struct.unpack('<11sc4xBB14x', f.read(32))
        name = name.replace(b'\0', b'')  # eliminate NULs from string
        fields.append((name, typ, size, deci))
    yield [field[0] for field in fields]
    yield [tuple(field[1:]) for field in fields]

    terminator = f.read(1)
    if terminator != b'\r':
        logger.error('Invalid DBF terminator: %s', terminator)
        raise ValueError(f'Invalid DBF terminator {terminator}')

    fields.insert(0, (b'DeletionFlag', b'C', 1, 0))
    fmt = ''.join([f'{fieldinfo[2]}s' for fieldinfo in fields])
    fmtsiz = struct.calcsize(fmt)
    for i in range(numrec):
        record = struct.unpack(fmt, f.read(fmtsiz))
        if record[0] != b' ':
            continue  # deleted record
        result = []
        for (name, typ, size, deci), value in itertools.zip_longest(fields, record):
            if name == b'DeletionFlag':
                continue
            if typ == b"N":
                value = value.replace(b'\0', b'').lstrip()
                if value == b'':
                    value = 0
                elif deci:
                    value = decimal.Decimal(value)
                else:
                    value = int(value)
            elif typ == b'D':
                y, m, d = int(value[:4]), int(value[4:6]), int(value[6:8])
                value = datetime.date(y, m, d)
            elif typ == b'L':
                value = (value in b'YyTt' and b'T') or (value in b'NnFf' and b'F') or b'?'
            result.append(value)
        yield result
