import os
import sys
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, hash_password
from flask_babel import Babel


db = SQLAlchemy()
security = Security()


def create_app():

    app = Flask(__name__, instance_relative_config=False)

    app.config.from_pyfile('config.py')

    app.debug = True

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    Babel(app)

    db.init_app(app)

    from .models import User, Role
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, user_datastore)

    with app.app_context():
        db.create_all()
        if not user_datastore.find_user(email="test@example.com"):
            user_datastore.create_user(
                email="test@example.com",
                username="test",
                password=hash_password("test567")
            )
            db.session.commit()

    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify({"code": 404, "message": "Not Found"}), 404

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
