#!/usr/bin/env python

import argparse
from os import environ
from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy


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

AENEAS_DB_URI = environ.get('AENEAS_DB_URI', 'sqlite://')


def generate_app(db_uri=AENEAS_DB_URI):

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    db = app.db = SQLAlchemy(app)

    class Report(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        raw = db.Column(db.String(4000))

        def __init__(self, raw):
            self.raw = raw

    @app.route('/v1.0/reports', methods=['POST'])
    def submit_report():
        if request.content_type == 'application/x-www-form-urlencoded':
            raw = request.form.keys()[0]
        else:
            raw = request.data
        report = Report(raw)
        db.session.add(report)
        db.session.commit()
        return '', 201

    return app


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug',
                        help='Run Flask in debug mode, with auto-reload and '
                             'debugger page on errors. Default is {}. '
                             'Environment variable is AENEAS_DEBUG.'.format(
                                AENEAS_DEBUG),
                        action='store_true',
                        default=AENEAS_DEBUG)
    parser.add_argument('--port',
                        help='The port on which to accept incoming HTTP '
                             'requests. Default is {}. Environment variables '
                             'is AENEAS_PORT.'.format(AENEAS_PORT),
                        action='store', default=AENEAS_PORT, type=int)
    parser.add_argument('--db-uri',
                        help='The URI for the database, to be passed to '
                             'SQLAlchemy. Default is {}. Environment variable '
                             'is AENEAS_DB_URI.'.format(AENEAS_DB_URI),
                        action='store', default=AENEAS_DB_URI)
    parser.add_argument('--create-db', help='Initialize the database schema '
                                            'and then exit.',
                        action='store_true')

    args = parser.parse_args()

    print('Debug: {}'.format(args.debug))
    print('Port: {}'.format(args.port))
    print('DB URI: {}'.format(args.db_uri))

    app = generate_app(db_uri=args.db_uri)

    if args.create_db:
        print('Setting up the database')
        app.db.create_all()
    else:
        app.run(debug=args.debug, port=args.port)
