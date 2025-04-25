from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from app.models import db
from .program_routes import program_bp
from .client_routes import client_bp

db=SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://your_user:your_password@localhost/your_db_name'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)


    with app.app_context():
        db.create_all()

    app.register_blueprint(program_bp)
    app.register_blueprint(client_bp)

    return app