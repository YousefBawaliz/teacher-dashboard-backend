"""
Security utilities for the Teacher Dashboard application.
Contains decorators and helpers for authentication and authorization.
"""
from functools import wraps
from flask import current_app, jsonify, request, g
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash

def teacher_required(f):
    """
    Decorator to restrict access to teachers only.
    Must be used with Flask-Login's login_required decorator.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        
        if current_user.role != 'teacher':
            return jsonify({"status": "error", "message": "Teacher access required"}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """
    Decorator to restrict access to students only.
    Must be used with Flask-Login's login_required decorator.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        
        if current_user.role != 'student':
            return jsonify({"status": "error", "message": "Student access required"}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def resource_owner_required(model, id_param='id', owner_field='teacher_id'):
    """
    Factory for decorators that check if the current user owns a resource.
    
    Args:
        model: The SQLAlchemy model to check ownership against
        id_param: The parameter name in the route that contains the resource ID
        owner_field: The field name in the model that contains the owner's ID
    
    Returns:
        A decorator function that checks resource ownership
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"status": "error", "message": "Authentication required"}), 401
            
            # Get the resource ID from the route parameters
            resource_id = kwargs.get(id_param)
            if not resource_id:
                return jsonify({"status": "error", "message": "Resource ID not provided"}), 400
            
            # Get the resource from the database
            resource = model.query.get(resource_id)
            if not resource:
                return jsonify({"status": "error", "message": "Resource not found"}), 404
            
            # Check if the current user owns the resource
            if getattr(resource, owner_field) != current_user.id:
                return jsonify({"status": "error", "message": "Access denied to this resource"}), 403
            
            # Store the resource in g for the view function to use
            g.resource = resource
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def hash_password(password):
    """
    Generate a secure hash of the password.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        A secure hash of the password
    """
    return generate_password_hash(password)


def verify_password(password_hash, password):
    """
    Verify that a password matches a hash.
    
    Args:
        password_hash: The stored password hash
        password: The plain text password to verify
        
    Returns:
        True if the password matches, False otherwise
    """
    return check_password_hash(password_hash, password)