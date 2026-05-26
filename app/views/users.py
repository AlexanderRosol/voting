import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from passlib.hash import bcrypt
from sqlalchemy.exc import IntegrityError

try:
    from email_validator import validate_email, EmailNotValidError
    HAS_EMAIL_VALIDATOR = True
except ImportError:
    HAS_EMAIL_VALIDATOR = False

from ..app import db
from ..models import User

bp = Blueprint('bp_users', __name__)


def _error(code, message):
    return jsonify({"code": code, "message": message}), code


def _serialize_user(u):
    return {
        'id': str(u.id),
        'username': u.username,
        'email': u.email,
        'created_at': u.created_at.isoformat() if u.created_at else None
    }


def _validate_email(value):
    if not isinstance(value, str) or not (1 <= len(value) <= 255):
        return False
    if HAS_EMAIL_VALIDATOR:
        try:
            validate_email(value, check_deliverability=False)
        except EmailNotValidError:
            return False
        return True
    return '@' in value and '.' in value.split('@')[-1]


def _current_user_id():
    try:
        return uuid.UUID(get_jwt_identity())
    except (TypeError, ValueError, AttributeError):
        return None


def _parse_json():
    try:
        data = request.get_json(force=True, silent=False)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


@bp.route('/users', methods=['GET'])
@jwt_required()
def users_get():
    users = User.query.order_by(User.created_at.asc()).all()
    return jsonify([_serialize_user(u) for u in users]), 200


@bp.route('/users', methods=['POST'])
def users_post():
    data = _parse_json()
    if data is None:
        return _error(400, "Invalid JSON payload")

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not isinstance(username, str) or not (1 <= len(username) <= 30):
        return _error(400, "username is required (1-30 chars)")
    if not _validate_email(email):
        return _error(400, "email is required and must be valid")
    if not isinstance(password, str) or len(password) < 6:
        return _error(400, "password is required (min 6 chars)")

    user = User(
        username=username,
        email=email,
        password=bcrypt.hash(password)
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error(400, "username or email already exists")

    return jsonify(_serialize_user(user)), 201


@bp.route('/users/<uuid:user_id>', methods=['GET'])
@jwt_required()
def users_show_get(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return _error(404, "User not found")
    return jsonify(_serialize_user(user)), 200


@bp.route('/users/<uuid:user_id>', methods=['PUT'])
@jwt_required()
def users_put(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return _error(404, "User not found")

    current = _current_user_id()
    if current is None or user.id != current:
        return _error(403, "Not allowed")

    data = _parse_json()
    if data is None:
        return _error(400, "Invalid JSON payload")

    username = data.get('username')
    email = data.get('email')

    if not isinstance(username, str) or not (1 <= len(username) <= 30):
        return _error(400, "username is required (1-30 chars)")
    if not _validate_email(email):
        return _error(400, "email is required and must be valid")

    user.username = username
    user.email = email
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error(400, "username or email already exists")

    return jsonify(_serialize_user(user)), 200


@bp.route('/users/<uuid:user_id>', methods=['DELETE'])
@jwt_required()
def users_delete(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return _error(404, "User not found")

    current = _current_user_id()
    if current is None or user.id != current:
        return _error(403, "Not allowed")

    db.session.delete(user)
    db.session.commit()
    return '', 204
