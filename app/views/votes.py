import uuid
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..app import db
from ..models import Vote

bp = Blueprint('bp_votes', __name__)


def _error(code, message):
    return jsonify({"code": code, "message": message}), code


def _serialize_vote(v):
    return {
        'id': str(v.id),
        'user_id': str(v.user_id),
        'poll_id': str(v.poll_id),
        'option_id': str(v.option_id),
        'voted_at': v.voted_at.isoformat() if v.voted_at else None
    }


def _current_user_id():
    try:
        return uuid.UUID(get_jwt_identity())
    except (TypeError, ValueError, AttributeError):
        return None


@bp.route('/votes/<uuid:vote_id>', methods=['GET'])
@jwt_required()
def votes_show_get(vote_id):
    vote = db.session.get(Vote, vote_id)
    if vote is None:
        return _error(404, "Vote not found")
    return jsonify(_serialize_vote(vote)), 200


@bp.route('/votes/<uuid:vote_id>', methods=['DELETE'])
@jwt_required()
def votes_delete(vote_id):
    vote = db.session.get(Vote, vote_id)
    if vote is None:
        return _error(404, "Vote not found")

    current = _current_user_id()
    if current is None or vote.user_id != current:
        return _error(403, "Not allowed")

    db.session.delete(vote)
    db.session.commit()
    return '', 204
