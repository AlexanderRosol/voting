import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flasgger import Swagger


db = SQLAlchemy()
jwt = JWTManager()


def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=False)

    app.config.from_pyfile('config.py')

    if test_config:
        app.config.update(test_config)

    app.debug = app.config.get('DEBUG', True)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    jwt.init_app(app)

    Swagger(app, template_file=os.path.join(os.path.dirname(__file__), 'openapi.yaml'))

    from . import models  # noqa: F401 - register mappers

    if not app.config.get('TESTING'):
        with app.app_context():
            db.create_all()

    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify({"code": 404, "message": "Not Found"}), 404

    @jwt.unauthorized_loader
    def jwt_missing_token(reason):
        return jsonify({"code": 401, "message": "Authentication required"}), 401

    @jwt.invalid_token_loader
    def jwt_invalid_token(reason):
        return jsonify({"code": 401, "message": "Invalid token"}), 401

    @jwt.expired_token_loader
    def jwt_expired_token(jwt_header, jwt_payload):
        return jsonify({"code": 401, "message": "Token expired"}), 401

    from .views.auth import bp as bp_auth
    app.register_blueprint(bp_auth)

    from .views.users import bp as bp_users
    app.register_blueprint(bp_users)

    from .views.polls import bp as bp_polls
    app.register_blueprint(bp_polls)

    from .views.votes import bp as bp_votes
    app.register_blueprint(bp_votes)

    @app.after_request
    def allow_cors(response):
        import re
        http_origin = request.environ.get('HTTP_ORIGIN', None)
        http_access_ctrl_req_headers = request.environ.get(
            'HTTP_ACCESS_CONTROL_REQUEST_HEADERS',
            None
        )
        if http_origin and re.search(r'^[a-zA-Z0-9\-\_\/\:\.]+$', http_origin, re.DOTALL):
            response.headers['Access-Control-Allow-Origin'] = http_origin
            response.headers['Access-Control-Allow-Credentials'] = "true"
            response.headers['Access-Control-Allow-Methods'] = ("GET, POST, PUT, PATCH, DELETE, "
                                                                "OPTIONS")
            response.headers['Access-Control-Expose-Headers'] = ("*, Content-Disposition, "
                                                                 "Content-Length, "
                                                                 "X-Uncompressed-Content-Length")
            if http_access_ctrl_req_headers:
                response.headers['Access-Control-Allow-Headers'] = http_access_ctrl_req_headers

        return response

    return app
