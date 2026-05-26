import uuid
import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from ..app import db
from ..models import Poll, PollOption, Vote

bp = Blueprint('bp_polls', __name__)


ALLOWED_STATUSES = ('active', 'closed', 'draft')


def _error(code, message):
    return jsonify({"code": code, "message": message}), code


def _serialize_poll(p):
    return {
        'id': str(p.id),
        'title': p.title,
        'description': p.description,
        'created_by': str(p.created_by),
        'status': p.status,
        'created_at': p.created_at.isoformat() if p.created_at else None,
        'expires_at': p.expires_at.isoformat() if p.expires_at else None
    }


def _serialize_option(o):
    return {
        'id': str(o.id),
        'poll_id': str(o.poll_id),
        'option_text': o.option_text,
        'display_order': o.display_order
    }


def _serialize_vote(v):
    return {
        'id': str(v.id),
        'user_id': str(v.user_id),
        'poll_id': str(v.poll_id),
        'option_id': str(v.option_id),
        'voted_at': v.voted_at.isoformat() if v.voted_at else None
    }


def _parse_json():
    try:
        data = request.get_json(force=True, silent=False)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _parse_datetime(value):
    if value is None:
        return None
    if not isinstance(value, str):
        return False
    try:
        return datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return False


def _parse_uuid(value):
    if not isinstance(value, str):
        return None
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


def _current_user_id():
    try:
        return uuid.UUID(get_jwt_identity())
    except (TypeError, ValueError, AttributeError):
        return None


@bp.route('/polls', methods=['GET'])
def polls_get():
    polls = Poll.query.order_by(Poll.created_at.desc()).all()
    return jsonify([_serialize_poll(p) for p in polls]), 200


@bp.route('/polls', methods=['POST'])
@jwt_required()
def polls_post():
    data = _parse_json()
    if data is None:
        return _error(400, "Invalid JSON payload")

    title = data.get('title')
    if not isinstance(title, str) or not (1 <= len(title) <= 120):
        return _error(400, "title is required (1-120 chars)")

    description = data.get('description')
    if description is not None and not isinstance(description, str):
        return _error(400, "description must be a string")

    status = data.get('status', 'active')
    if status not in ALLOWED_STATUSES:
        return _error(400, f"status must be one of {ALLOWED_STATUSES}")

    expires_at = _parse_datetime(data.get('expires_at'))
    if expires_at is False:
        return _error(400, "expires_at must be ISO-8601 datetime")

    user_id = _current_user_id()
    if user_id is None:
        return _error(401, "Authentication required")

    poll = Poll(
        title=title,
        description=description,
        created_by=user_id,
        status=status,
        expires_at=expires_at
    )
    db.session.add(poll)
    db.session.commit()
    return jsonify(_serialize_poll(poll)), 201


@bp.route('/polls/<uuid:poll_id>', methods=['GET'])
def polls_show_get(poll_id):
    poll = db.session.get(Poll, poll_id)
    if poll is None:
        return _error(404, "Poll not found")
    return jsonify(_serialize_poll(poll)), 200


@bp.route('/polls/<uuid:poll_id>', methods=['PATCH'])
@jwt_required()
def polls_patch(poll_id):
    poll = db.session.get(Poll, poll_id)
    if poll is None:
        return _error(404, "Poll not found")

    current = _current_user_id()
    if current is None or poll.created_by != current:
        return _error(403, "Not allowed")

    data = _parse_json()
    if data is None:
        return _error(400, "Invalid JSON payload")

    if 'title' in data:
        if not isinstance(data['title'], str) or not (1 <= len(data['title']) <= 120):
            return _error(400, "title must be a string (1-120 chars)")
        poll.title = data['title']

    if 'description' in data:
        if data['description'] is not None and not isinstance(data['description'], str):
            return _error(400, "description must be a string")
        poll.description = data['description']

    if 'status' in data:
        if data['status'] not in ALLOWED_STATUSES:
            return _error(400, f"status must be one of {ALLOWED_STATUSES}")
        poll.status = data['status']

    if 'expires_at' in data:
        parsed = _parse_datetime(data['expires_at'])
        if parsed is False:
            return _error(400, "expires_at must be ISO-8601 datetime")
        poll.expires_at = parsed

    db.session.add(poll)
    db.session.commit()
    return jsonify(_serialize_poll(poll)), 200


@bp.route('/polls/<uuid:poll_id>', methods=['DELETE'])
@jwt_required()
def polls_delete(poll_id):
    poll = db.session.get(Poll, poll_id)
    if poll is None:
        return _error(404, "Poll not found")

    current = _current_user_id()
    if current is None or poll.created_by != current:
        return _error(403, "Not allowed")

    db.session.delete(poll)
    db.session.commit()
    return '', 204


@bp.route('/polls/<uuid:poll_id>/options', methods=['GET'])
def polls_options_get(poll_id):
    poll = db.session.get(Poll, poll_id)
    if poll is None:
        return _error(404, "Poll not found")

    options = PollOption.query.filter(
        PollOption.poll_id == poll.id
    ).order_by(PollOption.display_order.asc()).all()

    return jsonify([_serialize_option(o) for o in options]), 200


@bp.route('/polls/<uuid:poll_id>/options', methods=['POST'])
@jwt_required()
def polls_options_post(poll_id):
    poll = db.session.get(Poll, poll_id)
    if poll is None:
        return _error(404, "Poll not found")

    current = _current_user_id()
    if current is None or poll.created_by != current:
        return _error(403, "Not allowed")

    data = _parse_json()
    if data is None:
        return _error(400, "Invalid JSON payload")

    option_text = data.get('option_text')
    if not isinstance(option_text, str) or not (1 <= len(option_text) <= 100):
        return _error(400, "option_text is required (1-100 chars)")

    display_order_raw = data.get('display_order', 1)
    try:
        display_order = int(display_order_raw)
    except (TypeError, ValueError):
        return _error(400, "display_order must be an integer")

    option = PollOption(
        poll_id=poll.id,
        option_text=option_text,
        display_order=display_order
    )
    db.session.add(option)
    db.session.commit()
    return jsonify(_serialize_option(option)), 201


@bp.route('/polls/<uuid:poll_id>/votes', methods=['GET'])
@jwt_required()
def polls_votes_get(poll_id):
    poll = db.session.get(Poll, poll_id)
    if poll is None:
        return _error(404, "Poll not found")

    votes = Vote.query.filter(Vote.poll_id == poll.id).order_by(Vote.voted_at.asc()).all()
    return jsonify([_serialize_vote(v) for v in votes]), 200


@bp.route('/polls/<uuid:poll_id>/votes', methods=['POST'])
@jwt_required()
def polls_votes_post(poll_id):
    poll = db.session.get(Poll, poll_id)
    if poll is None:
        return _error(404, "Poll not found")

    data = _parse_json()
    if data is None:
        return _error(400, "Invalid JSON payload")

    option_id = _parse_uuid(data.get('option_id'))
    if option_id is None:
        return _error(400, "option_id must be a valid UUID")

    option = db.session.get(PollOption, option_id)
    if option is None or option.poll_id != poll.id:
        return _error(404, "Option not found for this poll")

    user_id = _current_user_id()
    if user_id is None:
        return _error(401, "Authentication required")

    vote = Vote(user_id=user_id, poll_id=poll.id, option_id=option.id)
    db.session.add(vote)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error(409, "User already voted in this poll")

    return jsonify(_serialize_vote(vote)), 201


@bp.route('/polls/<uuid:poll_id>/results', methods=['GET'])
def polls_results_get(poll_id):
    poll = db.session.get(Poll, poll_id)
    if poll is None:
        return _error(404, "Poll not found")

    counts = dict(
        db.session.query(Vote.option_id, func.count(Vote.id))
        .filter(Vote.poll_id == poll.id)
        .group_by(Vote.option_id)
        .all()
    )

    options = PollOption.query.filter(
        PollOption.poll_id == poll.id
    ).order_by(PollOption.display_order.asc()).all()

    return jsonify({
        'poll': _serialize_poll(poll),
        'options': [
            {'option': _serialize_option(o), 'votes': int(counts.get(o.id, 0))}
            for o in options
        ]
    }), 200
