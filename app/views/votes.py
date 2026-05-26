from flask import Blueprint, request, current_app, g, render_template, flash, redirect, url_for, jsonify
from flask_security import current_user, login_required

from ..app import db
from ..models import Vote

bp = Blueprint('bp_votes', __name__)


@bp.route('/votes/<uuid:vote_id>', methods=['GET'])
@login_required
def votes_show_get(vote_id):
    vote = Vote.query.get_or_404(vote_id)

    return jsonify({
        'id': str(vote.id),
        'user_id': str(vote.user_id),
        'poll_id': str(vote.poll_id),
        'option_id': str(vote.option_id),
        'voted_at': vote.voted_at
    })


@bp.route('/votes/<uuid:vote_id>', methods=['DELETE'])
@login_required
def votes_delete(vote_id):
    vote = Vote.query.get_or_404(vote_id)

    if vote.user_id == current_user.id:
        db.session.delete(vote)
        db.session.commit()
        return '', 204
    else:
        return 'You are not the author of this vote.', 400
