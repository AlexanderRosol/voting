import datetime
import uuid
import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, relationship
from flask_security import UserMixin, RoleMixin
from .app import db


class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id      = mapped_column(sa.Integer(), primary_key=True)
    user_id = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey('user.id'))
    role_id = mapped_column(sa.Integer(), sa.ForeignKey('role.id'))


class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id          = mapped_column(sa.Integer(), primary_key=True)
    name        = mapped_column(sa.String(80), unique=True)
    description = mapped_column(sa.String(255))
    users       = relationship('User', secondary='roles_users', back_populates="roles", lazy=True)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id                = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email             = mapped_column(sa.String(255), unique=True, nullable=False)
    username          = mapped_column(sa.String(30), unique=True, nullable=False)
    password          = mapped_column(sa.String(255), nullable=False)
    last_login_at     = mapped_column(sa.DateTime())
    current_login_at  = mapped_column(sa.DateTime())
    last_login_ip     = mapped_column(sa.String(100))
    current_login_ip  = mapped_column(sa.String(100))
    login_count       = mapped_column(sa.Integer())
    active            = mapped_column(sa.Boolean())
    fs_uniquifier     = mapped_column(sa.String(255), unique=True, nullable=False)
    confirmed_at      = mapped_column(sa.DateTime())
    created_at        = mapped_column(sa.DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow)
    roles             = relationship('Role', secondary='roles_users', back_populates="users", lazy=True)
    polls             = relationship('Poll', back_populates="creator", lazy=True)
    votes             = relationship('Vote', back_populates="user", lazy=True)


class Poll(db.Model):
    __tablename__ = 'poll'
    __table_args__ = (
        sa.CheckConstraint("status IN ('active', 'closed', 'draft')", name='chk_poll_status'),
    )
    id          = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title       = mapped_column(sa.String(120), nullable=False)
    description = mapped_column(sa.Text(), nullable=True)
    created_by  = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    status      = mapped_column(sa.String(10), nullable=False, default='active')
    created_at  = mapped_column(sa.DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow)
    expires_at  = mapped_column(sa.DateTime(timezone=True), nullable=True)
    creator     = relationship("User", back_populates="polls", lazy=False)
    options     = relationship("PollOption", back_populates="poll", lazy=True, cascade='all, delete-orphan')
    votes       = relationship("Vote", back_populates="poll", lazy=True, cascade='all, delete-orphan')


class PollOption(db.Model):
    __tablename__ = 'poll_option'
    id            = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poll_id       = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey('poll.id', ondelete='CASCADE'), nullable=False)
    option_text   = mapped_column(sa.String(100), nullable=False)
    display_order = mapped_column(sa.SmallInteger(), nullable=False, default=1)
    poll          = relationship("Poll", back_populates="options", lazy=False)
    votes         = relationship("Vote", back_populates="option", lazy=True, cascade='all, delete-orphan')


class Vote(db.Model):
    __tablename__ = 'vote'
    __table_args__ = (
        sa.UniqueConstraint('user_id', 'poll_id', name='uq_votes_user_poll'),
    )
    id        = mapped_column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id   = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    poll_id   = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey('poll.id', ondelete='CASCADE'), nullable=False)
    option_id = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey('poll_option.id', ondelete='CASCADE'), nullable=False)
    voted_at  = mapped_column(sa.DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow)
    user      = relationship("User", back_populates="votes", lazy=False)
    poll      = relationship("Poll", back_populates="votes", lazy=False)
    option    = relationship("PollOption", back_populates="votes", lazy=False)
