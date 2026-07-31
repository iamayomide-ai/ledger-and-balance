import os
from flask import Flask
from .models import db


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "siwes-bank-recon-demo-key"

    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, "..", "instance", "recon.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB upload cap

    db.init_app(app)

    from .routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app
