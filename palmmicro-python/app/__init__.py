"""Palmmicro Python Application."""

import os
from urllib.parse import quote_plus
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # Database configuration
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '3306')
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', '')
    db_name = os.environ.get('DB_NAME', 'palmmicro')

    # URL-encode password to handle special characters
    encoded_password = quote_plus(db_password)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=f"mysql+pymysql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Initialize database
    db.init_app(app)

    # Flask-SQLAlchemy 3.x compatibility: restore 2.x-style shortcuts
    # In 2.x: db.query/execute/commit/add worked directly on db instance
    # In 3.x: these are removed, must use db.session.* instead
    _session = db.session
    for _name, _fn in [
        ('query', lambda *e, **kw: _session.query(*e, **kw)),
        ('execute', lambda s, p=None: _session.execute(s, p or {})),
        ('commit', lambda: _session.commit()),
        ('add', lambda o: _session.add(o)),
        ('rollback', lambda: _session.rollback()),
    ]:
        if not callable(getattr(db, _name, None)):
            setattr(db, _name, _fn)

    from app import routes
    app.register_blueprint(routes.bp)

    return app
