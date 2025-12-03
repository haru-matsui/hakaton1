from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='student')  # student or teacher
    avatar = db.Column(db.String(255), default='default_avatar.png')
    bio = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    conspectuses = db.relationship('Conspectus', backref='author', lazy=True, foreign_keys='Conspectus.author_id')
    ratings = db.relationship('Rating', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    reports = db.relationship('Report', backref='reporter', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_total_likes(self):
        """Get total likes across all user's conspectuses"""
        total = 0
        for conspectus in self.conspectuses:
            total += conspectus.get_rating()
        return total
    
    def __repr__(self):
        return f'<User {self.username}>'


class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<Tag {self.name}>'


class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<Subject {self.name}>'


# Association table for many-to-many relationship between Conspectus and Tag
conspectus_tags = db.Table('conspectus_tags',
    db.Column('conspectus_id', db.Integer, db.ForeignKey('conspectuses.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)


class Conspectus(db.Model):
    __tablename__ = 'conspectuses'
    
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    visibility = db.Column(db.String(20), default='public')  # public, link, private
    share_link = db.Column(db.String(100), unique=True, nullable=True)
    is_draft = db.Column(db.Boolean, default=True)
    views_count = db.Column(db.Integer, default=0)
    downloads_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subject = db.relationship('Subject', backref='conspectuses')
    tags = db.relationship('Tag', secondary=conspectus_tags, backref='conspectuses')
    versions = db.relationship('ConspectusVersion', backref='conspectus', lazy=True, order_by='ConspectusVersion.created_at.desc()')
    ratings = db.relationship('Rating', backref='conspectus', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='conspectus', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='conspectus', lazy=True, cascade='all, delete-orphan')
    coauthors = db.relationship('CoAuthor', backref='conspectus', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='conspectus', lazy=True, cascade='all, delete-orphan')
    
    def generate_share_link(self):
        """Generate unique share link"""
        self.share_link = secrets.token_urlsafe(16)
    
    def get_rating(self):
        """Calculate total rating (likes - dislikes)"""
        total = 0
        for rating in self.ratings:
            total += rating.vote
        return total
    
    def get_likes_count(self):
        """Get number of likes"""
        return sum(1 for r in self.ratings if r.vote == 1)
    
    def get_dislikes_count(self):
        """Get number of dislikes"""
        return sum(1 for r in self.ratings if r.vote == -1)
    
    def user_rating(self, user_id):
        """Get user's rating for this conspectus"""
        rating = Rating.query.filter_by(conspectus_id=self.id, user_id=user_id).first()
        return rating.vote if rating else 0
    
    def __repr__(self):
        return f'<Conspectus {self.title}>'


class ConspectusVersion(db.Model):
    __tablename__ = 'conspectus_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    conspectus_id = db.Column(db.Integer, db.ForeignKey('conspectuses.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ConspectusVersion {self.id} of {self.conspectus_id}>'


class Rating(db.Model):
    __tablename__ = 'ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    conspectus_id = db.Column(db.Integer, db.ForeignKey('conspectuses.id'), nullable=False)
    vote = db.Column(db.Integer, nullable=False)  # 1 for like, -1 for dislike
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure one vote per user per conspectus
    __table_args__ = (db.UniqueConstraint('user_id', 'conspectus_id', name='_user_conspectus_uc'),)
    
    def __repr__(self):
        return f'<Rating user={self.user_id} conspectus={self.conspectus_id} vote={self.vote}>'


class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    conspectus_id = db.Column(db.Integer, db.ForeignKey('conspectuses.id'), nullable=False)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    text = db.Column(db.Text, nullable=False)
    is_author_reply = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referential relationship for nested comments
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    def __repr__(self):
        return f'<Comment {self.id} by user {self.user_id}>'


class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    conspectus_id = db.Column(db.Integer, db.ForeignKey('conspectuses.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure one favorite per user per conspectus
    __table_args__ = (db.UniqueConstraint('user_id', 'conspectus_id', name='_user_conspectus_fav_uc'),)
    
    def __repr__(self):
        return f'<Favorite user={self.user_id} conspectus={self.conspectus_id}>'


class CoAuthor(db.Model):
    __tablename__ = 'coauthors'
    
    id = db.Column(db.Integer, primary_key=True)
    conspectus_id = db.Column(db.Integer, db.ForeignKey('conspectuses.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission_level = db.Column(db.String(20), default='edit')  # view, edit, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='coauthor_entries')
    
    # Ensure one coauthor entry per user per conspectus
    __table_args__ = (db.UniqueConstraint('user_id', 'conspectus_id', name='_user_conspectus_coauthor_uc'),)
    
    def __repr__(self):
        return f'<CoAuthor user={self.user_id} conspectus={self.conspectus_id}>'


class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    conspectus_id = db.Column(db.Integer, db.ForeignKey('conspectuses.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Report {self.id} status={self.status}>'
