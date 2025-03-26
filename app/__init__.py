"""
Application factory for the Teacher Dashboard application.
Creates and configures the Flask application.
"""
from flask import Flask, jsonify
from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_object="app.config.DevConfig"):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configure CORS - allow requests from frontend
    CORS(app, supports_credentials=True, resources={
        r"/api/*": {"origins": app.config.get('CORS_ORIGINS', '*')}
    })
    
    # Setup API with Flask-Smorest
    api = Api(app)
    
    # Configure login manager
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login."""
        return User.query.get(int(user_id))
    
    # Handle unauthorized access
    @login_manager.unauthorized_handler
    def unauthorized():
        """Handle unauthorized access attempts."""
        return jsonify({
            "status": "error",
            "message": "Authentication required"
        }), 401
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(api)
    
    # Create database tables if not exists (for development)
    with app.app_context():
        db.create_all()
    
    return app

def register_blueprints(api):
    """Register all API blueprints with the application."""
    from app.api.auth import auth_blp
    
    # Register blueprints with API
    api.register_blueprint(auth_blp)
    
    # Import and register class and course blueprints
    # Will be implemented in subsequent steps
    from app.api.classes import classes_blp
    from app.api.courses import courses_blp
    from app.api.students import students_blp
    
    api.register_blueprint(classes_blp)
    api.register_blueprint(courses_blp)
    api.register_blueprint(students_blp)

def register_error_handlers(app):
    """Register error handlers for the application."""
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            "status": "error",
            "message": "Bad request",
            "errors": getattr(error, "description", str(error))
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        return jsonify({
            "status": "error",
            "message": "Authentication required",
            "errors": getattr(error, "description", str(error))
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        return jsonify({
            "status": "error",
            "message": "Access denied",
            "errors": getattr(error, "description", str(error))
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            "status": "error",
            "message": "Resource not found",
            "errors": getattr(error, "description", str(error))
        }), 404
    
    @app.errorhandler(500)
    def server_error(error):
        """Handle 500 Internal Server Error errors."""
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "errors": getattr(error, "description", str(error))
        }), 500