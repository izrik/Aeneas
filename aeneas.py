#!/usr/bin/env python2

import argparse
from os import environ


def bool_from_str(s):
    if isinstance(s, basestring):
        s = s.lower()
    if s in ['true', 't', '1', 'y']:
        return True
    if s in ['false', 'f', '0', 'n']:
        return False
    return bool(s)


AENEAS_DEBUG = bool_from_str(environ.get('AENEAS_DEBUG', False))

DEFAULT_AENEAS_PORT = 4935
AENEAS_PORT = environ.get('AENEAS_PORT', DEFAULT_AENEAS_PORT)
try:
    AENEAS_PORT = int(AENEAS_PORT)
except:
    AENEAS_PORT = DEFAULT_AENEAS_PORT


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', help='Run Flask in debug mode, with '
                                        'auto-reload and debugger page on '
                                        'errors.',
                        action='store_true', default=AENEAS_DEBUG)
    parser.add_argument('--port', help='The port on which to accept incoming '
                                       'HTTP requests. Default is {}'.format(
                                            AENEAS_PORT),
                        action='store', default=AENEAS_PORT, type=int)

    args = parser.parse_args()

    print('aeneas.py')
