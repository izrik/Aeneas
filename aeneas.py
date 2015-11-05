#!/usr/bin/env python

import argparse
from os import environ
from flask import Flask, request, render_template, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
import json
import itertools
import datetime
from dateutil.parser import parse as dparse


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

DEFAULT_AENEAS_MAX_CONTENT_LENGTH = 4000
AENEAS_MAX_CONTENT_LENGTH = environ.get('AENEAS_MAX_CONTENT_LENGTH',
                                        DEFAULT_AENEAS_MAX_CONTENT_LENGTH)
try:
    AENEAS_MAX_CONTENT_LENGTH = int(AENEAS_MAX_CONTENT_LENGTH)
except:
    AENEAS_MAX_CONTENT_LENGTH = DEFAULT_AENEAS_MAX_CONTENT_LENGTH


def generate_app(db_uri=AENEAS_DB_URI,
                 max_content_length=AENEAS_MAX_CONTENT_LENGTH):

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['MAX_CONTENT_LENGTH'] = max_content_length
    db = app.db = SQLAlchemy(app)

    class Report(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        raw = db.Column(db.Text(128000), nullable=False)
        product = db.Column(db.String(100), nullable=False)
        version = db.Column(db.String(100), nullable=False)
        timestamp = db.Column(db.DateTime, nullable=False)

        def __init__(self, raw, product, version, timestamp=None):
            self.raw = raw
            self.product = product
            self.version = version
            if timestamp is None:
                timestamp = datetime.datetime.utcnow()
            if isinstance(timestamp, basestring):
                timestamp = dparse(timestamp)
            self.timestamp = timestamp

        def to_dict(self):
            return {'id': self.id,
                    'raw': self.raw,
                    'product': self.product,
                    'version': self.version,
                    'timestamp': self.timestamp}

    @app.route('/v1.0/reports', methods=['POST'])
    def submit_report():
        if request.content_type != 'application/json':
            return ('Content-Type was "{}", but only "application/json" is '
                    'supported.'.format(request.content_type), 415)
        if len(request.data) > app.config['MAX_CONTENT_LENGTH']:
            return '', 413

        report_json = request.json

        if 'product' not in report_json:
            return 'No product specified', 400
        product = report_json['product']
        if not isinstance(product, basestring):
            return 'Product is wrong type', 400

        if 'version' not in report_json:
            return 'No version specified', 400
        version = report_json['version']
        if not isinstance(version, basestring):
            return 'Version is wrong type', 400

        if 'X-Real-IP' in request.headers:
            report_json['server_remote_ip'] = request.headers['X-Real-IP']
        else:
            report_json['server_remote_ip'] = request.remote_addr

        raw = json.dumps(report_json)

        report = Report(raw, product, version)
        db.session.add(report)
        db.session.commit()

        clean_up_report(report)
        db.session.add(report)
        db.session.commit()

        return '', 201

    def get_accept_type():
        best = request.accept_mimetypes.best_match(['application/json',
                                                    'text/html'])
        if (best == 'text/html' and request.accept_mimetypes[best] >=
                request.accept_mimetypes['application/json']):
            return 'html'
        elif (best == 'application/json' and request.accept_mimetypes[best] >=
                request.accept_mimetypes['text/html']):
            return 'json'
        else:
            return None

    @app.route('/v1.0/reports', methods=['GET'])
    def list_reports():
        accept = get_accept_type()
        if accept is None:
            return '', 406

        reports = Report.query.all()

        if accept == 'html':
            return render_template('list_reports.html', reports=reports,
                                   cycle=itertools.cycle)
        else:
            jreports = [json.loads(r.raw) for r in reports]
            return json.dumps(jreports), 200

    def clean_up_report(report):
        jraw = json.loads(report.raw)
        jraw['id'] = report.id
        report.raw = json.dumps(jraw)
        return report

    @app.route('/v1.0/reports/clean-up-all', methods=['GET'])
    def clean_up_all_reports():
        reports = Report.query.all()
        for report in reports:
            clean_up_report(report)
            db.session.add(report)
        db.session.commit()
        return redirect(url_for('list_reports'))

    @app.route('/v1.0/reports/<int:id>', methods=['GET'])
    def show_report(id):
        accept = get_accept_type()
        if accept is None:
            return '', 406

        report = Report.query.get(id)
        if report is None:
            return '', 404
        if accept == 'html':
            raw = json.dumps(json.loads(report.raw), indent=2)
            return render_template('show_report.html', report=report, raw=raw)
        return report.raw, 200

    @app.route('/v1.0/reports/<int:id>/download', methods=['GET'])
    def download_report(id):
        report = Report.query.get(id)
        if report is None:
            return '', 404
        return report.raw, 200

    @app.route('/v1.0/diagnostics/show-full-request')
    def show_full_request():
        req = request
        # raise ZeroDivisionError
        return render_template('show_full_request.html', request=request,
                               keys=dir(request), getattr=getattr)

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
    parser.add_argument('--max-content-length',
                        help='Limit the maximum size of an incoming request '
                             'body that will be accepted. Default is {}. '
                             'Environment variable is '
                             'AENEAS_MAX_CONTENT_LENGTH'.format(
                                AENEAS_MAX_CONTENT_LENGTH),
                        action='store', default=AENEAS_MAX_CONTENT_LENGTH,
                        type=int)

    args = parser.parse_args()

    print('Debug: {}'.format(args.debug))
    print('Port: {}'.format(args.port))
    print('DB URI: {}'.format(args.db_uri))
    print('Max Content Length: {}'.format(args.max_content_length))

    app = generate_app(db_uri=args.db_uri,
                       max_content_length=args.max_content_length)

    if args.create_db:
        print('Setting up the database')
        app.db.create_all()
    else:
        app.run(debug=args.debug, port=args.port)
