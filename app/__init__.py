from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate  # Import Flask-Migrate
from app.config import Config

def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(Config)
    
    if test_config:
        app.config.update(test_config)
         
    # Import db here to avoid circular import
    from app.models import db
    db.init_app(app)  # Initialize db here

    # Initialize Flask-Migrate
    migrate = Migrate(app, db)

    with app.app_context():
        db.create_all()

    # Register blueprints
    from .routes.program_routes import program_bp
    from .routes.client_routes import client_bp
    app.register_blueprint(program_bp)
    app.register_blueprint(client_bp)

    return app
