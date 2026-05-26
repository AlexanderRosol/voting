from flask import Blueprint, request, current_app, g, render_template, flash, redirect, url_for, jsonify
from flask_security import current_user, login_required, hash_password
from sqlalchemy.exc import IntegrityError

from ..app import db, security
from ..models import User

bp = Blueprint('bp_users', __name__)


@bp.route('/users', methods=['GET'])
@login_required
def users_get():
    users = User.query.order_by(User.created_at.asc()).all()

    results = []
    for u in users:
        results.append({
            'id': str(u.id),
            'username': u.username,
            'email': u.email,
            'created_at': u.created_at
        })

    return jsonify(results)


@bp.route('/users', methods=['POST'])
def users_post():
    data = request.get_json(force=True)

    if 'username' not in data or not (1 <= len(data['username']) <= 30):
        return 'Username is incorrect or was not given.', 400
    if 'email' not in data or not (1 <= len(data['email']) <= 255) or '@' not in data['email']:
        return 'Email is incorrect or was not given.', 400
    if 'password' not in data or len(data['password']) < 6:
        return 'Password is incorrect or was not given.', 400

    user_datastore = security.datastore
    try:
        user = user_datastore.create_user(
            username=data['username'],
            email=data['email'],
            password=hash_password(data['password'])
        )
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return 'Username or email already exists.', 400

    return jsonify({
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at
    }), 201


@bp.route('/users/<uuid:user_id>', methods=['GET'])
@login_required
def users_show_get(user_id):
    user = User.query.get_or_404(user_id)

    return jsonify({
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at
    })


@bp.route('/users/<uuid:user_id>', methods=['PUT'])
@login_required
def users_put(user_id):
    user = User.query.get_or_404(user_id)

    if user.id != current_user.id:
        return 'You are not allowed to update this user.', 400

    data = request.get_json(force=True)

    if 'username' not in data or not (1 <= len(data['username']) <= 30):
        return 'Username is incorrect or was not given.', 400
    if 'email' not in data or not (1 <= len(data['email']) <= 255) or '@' not in data['email']:
        return 'Email is incorrect or was not given.', 400

    user.username = data['username']
    user.email = data['email']
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return 'Username or email already exists.', 400

    return jsonify({
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at
    })


@bp.route('/users/<uuid:user_id>', methods=['DELETE'])
@login_required
def users_delete(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        db.session.delete(user)
        db.session.commit()
        return '', 204
    else:
        return 'You are not allowed to delete this user.', 400
