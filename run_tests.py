#!/usr/bin/env python

import unittest
import argparse
import logging
from aeneas import generate_app
import json


class MaxContentLengthUnspecifiedTest(unittest.TestCase):

    def setUp(self):
        self.app = generate_app(db_uri='sqlite:///run_tests.db')
        self.app.db.create_all()

    def test_4000_should_be_ok(self):
        with self.app.test_client() as tc:
            resp = tc.post('/v1.0/reports', data=json.dumps(
                {'product': 'a', 'version': '1.0', 'data': 'x' * 3954}),
                           content_type='application/json')
            self.assertEqual(201, resp.status_code)

    def test_4001_should_fail(self):
        with self.app.test_client() as tc:
            resp = tc.post('/v1.0/reports', data=json.dumps(
                {'product': 'a', 'version': '1.0', 'data': 'x' * 3955}),
                           content_type='application/json')
            self.assertEqual(413, resp.status_code)


class MaxContentLengthSpecifiedTest(unittest.TestCase):

    def setUp(self):
        self.app = generate_app(db_uri='sqlite:///run_tests.db',
                                max_content_length=100)
        self.app.db.create_all()

    def test_100_should_be_ok(self):
        with self.app.test_client() as tc:
            resp = tc.post('/v1.0/reports', data=json.dumps(
                {'product': 'a', 'version': '1.0', 'data': 'x' * 54}),
                           content_type='application/json')
            self.assertEqual(201, resp.status_code)

    def test_101_should_fail(self):
        with self.app.test_client() as tc:
            resp = tc.post('/v1.0/reports', data=json.dumps(
                {'product': 'a', 'version': '1.0', 'data': 'x' * 55}),
                           content_type='application/json')
            self.assertEqual(413, resp.status_code)


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--print-log', action='store_true',
                        help='Print the log.')
    args = parser.parse_args()

    if args.print_log:
        logging.basicConfig(level=logging.DEBUG,
                            format=('%(asctime)s %(levelname)s:%(name)s:'
                                    '%(funcName)s:'
                                    '%(filename)s(%(lineno)d):'
                                    '%(threadName)s(%(thread)d):%(message)s'))

    unittest.main(argv=[''])

if __name__ == '__main__':
    run()
