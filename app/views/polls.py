from flask import Blueprint, request, current_app, g, render_template, flash, redirect, url_for, jsonify
from flask_security import current_user, login_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
import datetime

from ..app import db
from ..models import Poll, PollOption, Vote

bp = Blueprint('bp_polls', __name__)


ALLOWED_STATUSES = ('active', 'closed', 'draft')


def _serialize_poll(poll):
    return {
        'id': str(poll.id),
        'title': poll.title,
        'description': poll.description,
        'created_by': str(poll.created_by),
        'status': poll.status,
        'created_at': poll.created_at,
        'expires_at': poll.expires_at
    }


def _serialize_option(option):
    return {
        'id': str(option.id),
        'poll_id': str(option.poll_id),
        'option_text': option.option_text,
        'display_order': option.display_order
    }


def _serialize_vote(vote):
    return {
        'id': str(vote.id),
        'user_id': str(vote.user_id),
        'poll_id': str(vote.poll_id),
        'option_id': str(vote.option_id),
        'voted_at': vote.voted_at
    }


def _parse_expires_at(value):
    if value is None:
        return None
    try:
        return datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return False


@bp.route('/polls', methods=['GET'])
def polls_get():
    polls = Poll.query.order_by(Poll.created_at.desc()).all()

    results = [_serialize_poll(p) for p in polls]

    return jsonify(results)


@bp.route('/polls', methods=['POST'])
@login_required
def polls_post():
    data = request.get_json(force=True)

    if 'title' not in data or not (1 <= len(data['title']) <= 120):
        return 'Title is incorrect or was not given.', 400

    status = data.get('status', 'active')
    if status not in ALLOWED_STATUSES:
        return 'Status is incorrect.', 400

    expires_at = _parse_expires_at(data.get('expires_at'))
    if expires_at is False:
        return 'expires_at is incorrect.', 400

    poll = Poll(
        title=data['title'],
        description=data.get('description'),
        created_by=current_user.id,
        status=status,
        expires_at=expires_at
    )
    db.session.add(poll)
    db.session.commit()

    return jsonify(_serialize_poll(poll)), 201


@bp.route('/polls/<uuid:poll_id>', methods=['GET'])
def polls_show_get(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    return jsonify(_serialize_poll(poll))


@bp.route('/polls/<uuid:poll_id>', methods=['PATCH'])
@login_required
def polls_patch(poll_id):
    poll = Poll.query.get_or_404(poll_id)

    if poll.created_by != current_user.id:
        return 'You are not the author of this poll.', 400

    data = request.get_json(force=True)

    if 'title' in data:
        if not (1 <= len(data['title']) <= 120):
            return 'Title is incorrect.', 400
        poll.title = data['title']

    if 'description' in data:
        poll.description = data['description']

    if 'status' in data:
        if data['status'] not in ALLOWED_STATUSES:
            return 'Status is incorrect.', 400
        poll.status = data['status']

    if 'expires_at' in data:
        parsed = _parse_expires_at(data['expires_at'])
        if parsed is False:
            return 'expires_at is incorrect.', 400
        poll.expires_at = parsed

    db.session.add(poll)
    db.session.commit()

    return jsonify(_serialize_poll(poll))


@bp.route('/polls/<uuid:poll_id>', methods=['DELETE'])
@login_required
def polls_delete(poll_id):
    poll = Poll.query.get_or_404(poll_id)

    if poll.created_by == current_user.id:
        db.session.delete(poll)
        db.session.commit()
        return '', 204
    else:
        return 'You are not the author of this poll.', 400


@bp.route('/polls/<uuid:poll_id>/options', methods=['GET'])
def polls_options_get(poll_id):
    poll = Poll.query.get_or_404(poll_id)

    options = PollOption.query.filter(
        PollOption.poll_id == poll.id
    ).order_by(PollOption.display_order.asc()).all()

    results = [_serialize_option(o) for o in options]

    return jsonify(results)


@bp.route('/polls/<uuid:poll_id>/options', methods=['POST'])
@login_required
def polls_options_post(poll_id):
    poll = Poll.query.get_or_404(poll_id)

    if poll.created_by != current_user.id:
        return 'You are not the author of this poll.', 400

    data = request.get_json(force=True)

    if 'option_text' not in data or not (1 <= len(data['option_text']) <= 100):
        return 'option_text is incorrect or was not given.', 400

    try:
        display_order = int(data.get('display_order', 1))
    except (ValueError, TypeError):
        return 'display_order is incorrect.', 400

    option = PollOption(
        poll_id=poll.id,
        option_text=data['option_text'],
        display_order=display_order
    )
    db.session.add(option)
    db.session.commit()

    return jsonify(_serialize_option(option)), 201


@bp.route('/polls/<uuid:poll_id>/votes', methods=['GET'])
@login_required
def polls_votes_get(poll_id):
    poll = Poll.query.get_or_404(poll_id)

    votes = Vote.query.filter(Vote.poll_id == poll.id).order_by(Vote.voted_at.asc()).all()

    results = [_serialize_vote(v) for v in votes]

    return jsonify(results)


@bp.route('/polls/<uuid:poll_id>/votes', methods=['POST'])
@login_required
def polls_votes_post(poll_id):
    poll = Poll.query.get_or_404(poll_id)

    data = request.get_json(force=True)

    if 'option_id' not in data:
        return 'option_id was not given.', 400

    try:
        option_uuid = data['option_id']
    except (ValueError, TypeError):
        return 'option_id is incorrect.', 400

    option = PollOption.query.get(option_uuid)
    if option is None or option.poll_id != poll.id:
        return jsonify({"code": 404, "message": "Poll or option not found"}), 404

    vote = Vote(
        user_id=current_user.id,
        poll_id=poll.id,
        option_id=option.id
    )
    db.session.add(vote)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return 'User already voted in this poll.', 409

    return jsonify(_serialize_vote(vote)), 201


@bp.route('/polls/<uuid:poll_id>/results', methods=['GET'])
def polls_results_get(poll_id):
    poll = Poll.query.get_or_404(poll_id)

    counts = dict(
        db.session.query(Vote.option_id, func.count(Vote.id))
        .filter(Vote.poll_id == poll.id)
        .group_by(Vote.option_id)
        .all()
    )

    options = PollOption.query.filter(
        PollOption.poll_id == poll.id
    ).order_by(PollOption.display_order.asc()).all()

    option_results = []
    for o in options:
        option_results.append({
            'option': _serialize_option(o),
            'votes': int(counts.get(o.id, 0))
        })

    return jsonify({
        'poll': _serialize_poll(poll),
        'options': option_results
    })
