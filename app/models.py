import datetime
import uuid
import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, relationship
from .app import db


class User(db.Model):
    __tablename__ = 'users'
    id         = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username   = mapped_column(sa.String(30), unique=True, nullable=False)
    email      = mapped_column(sa.String(255), unique=True, nullable=False)
    password   = mapped_column(sa.String(255), nullable=False)
    created_at = mapped_column(sa.DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow)
    polls      = relationship("Poll", back_populates="creator", lazy=True, cascade='all, delete-orphan')
    votes      = relationship("Vote", back_populates="user", lazy=True, cascade='all, delete-orphan')


class Poll(db.Model):
    __tablename__ = 'polls'
    __table_args__ = (
        sa.CheckConstraint("status IN ('active', 'closed', 'draft')", name='chk_poll_status'),
    )
    id          = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title       = mapped_column(sa.String(120), nullable=False)
    description = mapped_column(sa.Text(), nullable=True)
    created_by  = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status      = mapped_column(sa.String(10), nullable=False, default='active')
    created_at  = mapped_column(sa.DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow)
    expires_at  = mapped_column(sa.DateTime(timezone=True), nullable=True)
    creator     = relationship("User", back_populates="polls", lazy=False)
    options     = relationship("PollOption", back_populates="poll", lazy=True, cascade='all, delete-orphan')
    votes       = relationship("Vote", back_populates="poll", lazy=True, cascade='all, delete-orphan')


class PollOption(db.Model):
    __tablename__ = 'poll_options'
    id            = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poll_id       = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey('polls.id', ondelete='CASCADE'), nullable=False)
    option_text   = mapped_column(sa.String(100), nullable=False)
    display_order = mapped_column(sa.SmallInteger(), nullable=False, default=1)
    poll          = relationship("Poll", back_populates="options", lazy=False)
    votes         = relationship("Vote", back_populates="option", lazy=True, cascade='all, delete-orphan')


class Vote(db.Model):
    __tablename__ = 'votes'
    __table_args__ = (
        sa.UniqueConstraint('user_id', 'poll_id', name='uq_votes_user_poll'),
    )
    id        = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id   = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    poll_id   = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey('polls.id', ondelete='CASCADE'), nullable=False)
    option_id = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey('poll_options.id', ondelete='CASCADE'), nullable=False)
    voted_at  = mapped_column(sa.DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow)
    user      = relationship("User", back_populates="votes", lazy=False)
    poll      = relationship("Poll", back_populates="votes", lazy=False)
    option    = relationship("PollOption", back_populates="votes", lazy=False)
