from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from passlib.hash import bcrypt

from ..models import User

bp = Blueprint('bp_auth', __name__)


def _error(code, message):
    return jsonify({"code": code, "message": message}), code


@bp.route('/auth/token', methods=['POST'])
def auth_token_post():
    try:
        data = request.get_json(force=True, silent=False)
    except Exception:
        return _error(400, "Invalid JSON payload")

    if not isinstance(data, dict):
        return _error(400, "Invalid request payload")

    username = data.get('username')
    password = data.get('password')

    if not isinstance(username, str) or not username:
        return _error(400, "username is required")
    if not isinstance(password, str) or not password:
        return _error(400, "password is required")

    user = User.query.filter(User.username == username).one_or_none()
    if user is None or not bcrypt.verify(password, user.password):
        return _error(400, "Invalid credentials")

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token, "token_type": "bearer"}), 200
