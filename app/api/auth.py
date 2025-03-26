"""
Authentication API for the Teacher Dashboard application.
Provides endpoints for login, logout, and checking login status.
"""
from flask import Blueprint, request, jsonify, session
from flask_smorest import Blueprint, abort
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models.user import User
from app.schemas import LoginSchema, UserSchema, UserCreateSchema

auth_blp = Blueprint(
    'auth', 
    'auth', 
    url_prefix='/api',
    description='Authentication operations'
)

@auth_blp.route('/login', methods=['POST'])
@auth_blp.arguments(LoginSchema)
@auth_blp.response(200, UserSchema)
def login(login_data):
    """
    Log in a user with email and password.
    
    Returns:
        User object with authentication status
    """
    email = login_data.get('email')
    password = login_data.get('password')
    remember = login_data.get('remember', False)
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        abort(401, message="Invalid email or password")
    
    # Log in the user
    login_user(user, remember=remember)
    
    return jsonify({
        "status": "success",
        "message": "Login successful",
        "user": user.to_dict(),
        "success": True
    }), 200


@auth_blp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    Log out the current user.
    
    Returns:
        Success message
    """
    logout_user()
    
    return jsonify({
        "status": "success",
        "message": "Logout successful"
    })


@auth_blp.route('/isLoggedIn', methods=['GET'])
def is_logged_in():
    """
    Check if the user is logged in.
    
    Returns:
        Authentication status and user details if authenticated
    """
    if current_user.is_authenticated:
        return jsonify({
            "status": "success",
            "isAuthenticated": True,
            "user": current_user.to_dict()
        })
    else:
        return jsonify({
            "status": "success",
            "isAuthenticated": False,
            "user": None
        })


@auth_blp.route('/register', methods=['POST'])
@auth_blp.arguments(UserCreateSchema)
@auth_blp.response(201, UserSchema)
def register(user_data):
    """
    Register a new user.
    In a production application, this would typically be restricted to admins only.
    
    Returns:
        The created user object
    """
    # Check if the user already exists
    existing_user = User.query.filter_by(email=user_data['email']).first()
    if existing_user:
        abort(409, message="A user with this email already exists")
    
    # Create the new user
    user = User(
        email=user_data['email'],
        name=user_data['name'],
        role=user_data['role']
    )
    user.set_password(user_data['password'])
    
    # Add to database
    db.session.add(user)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, message=f"Error creating user: {str(e)}")
    
    return {
        "status": "success",
        "message": "User created successfully",
        "user": user.to_dict()
    }, 201


@auth_blp.route('/user', methods=['GET'])
@login_required
def get_current_user():
    """
    Get details of the currently logged-in user.
    
    Returns:
        The current user's details
    """
    return jsonify({
        "status": "success",
        "user": current_user.to_dict()
    })


@auth_blp.route('/seed', methods=['POST'])
def seed_database():
    """
    Seed the database with initial data.
    This endpoint is for development and testing purposes.
    
    Returns:
        Success message
    """
    # Check if there are already users in the database
    if User.query.count() > 0:
        return jsonify({
            "status": "error",
            "message": "Database already has users"
        }), 409
    
    # Create sample users
    teacher1 = User(
        email="teacher@example.com",
        name="Jane Teacher",
        role="teacher"
    )
    teacher1.set_password("password")
    
    teacher2 = User(
        email="teacher2@example.com",
        name="Mike Johnson",
        role="teacher"
    )
    teacher2.set_password("password")
    
    student1 = User(
        email="student@example.com",
        name="John Student",
        role="student"
    )
    student1.set_password("password")
    
    # Add more sample students
    students = [
        User(email="student1@example.com", name="Emily Parker", role="student"),
        User(email="student2@example.com", name="Michael Brown", role="student"),
        User(email="student3@example.com", name="Sophia Wilson", role="student"),
        User(email="student4@example.com", name="Daniel Lee", role="student"),
        User(email="student5@example.com", name="Olivia Martinez", role="student"),
        User(email="student6@example.com", name="James Taylor", role="student")
    ]
    
    for student in students:
        student.set_password("password")
    
    # Add all users to the database
    db.session.add(teacher1)
    db.session.add(teacher2)
    db.session.add(student1)
    
    for student in students:
        db.session.add(student)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Error seeding database: {str(e)}"
        }), 500
    
    return jsonify({
        "status": "success",
        "message": "Database seeded successfully",
        "data": {
            "teachers": 2,
            "students": 7
        }
    })