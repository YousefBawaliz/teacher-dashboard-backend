"""
Comprehensive test suite for Teacher Dashboard APIs.

This test suite covers authentication, courses, classes, and student APIs 
with thorough testing of various scenarios including:
- Successful operations
- Authorization checks
- Input validation
- Error handling
"""
import pytest
from flask import json
from datetime import date, timedelta
from app import create_app, db
from app.models.user import User
from app.models.course import Course
from app.models.class_model import Class
from app.models.associations import ClassStudent, ClassCourse

@pytest.fixture(scope='module')
def test_app():
    """Create a test application and database."""
    app = create_app('app.config.TestConfig')
    
    with app.app_context():
        db.create_all()
        
        # Create test users
        teacher = User(
            email='teacher_test@example.com',
            name='Test Teacher',
            role='teacher',
            password='testpassword'  # Use the __init__ parameter
        )
        
        student = User(
            email='student_test@example.com',
            name='Test Student',
            role='student',
            password='testpassword'  # Use the __init__ parameter
        )
        
        db.session.add(teacher)
        db.session.add(student)
        
        try:
            db.session.commit()
            # Verify user creation
            assert teacher.is_teacher, "Teacher role not set correctly"
            assert not student.is_teacher, "Student role incorrectly set as teacher"
            
            app.test_teacher_id = teacher.id
            app.test_student_id = student.id
        except Exception as e:
            db.session.rollback()
            raise
    
    yield app
    
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='module')
def test_client(test_app):
    """Create a test client for making requests."""
    with test_app.test_client() as client:
        # Enable preserving the cookies
        client.testing = True
        # Configure to follow redirects (which might occur during login)
        client.follow_redirects = True
        yield client


# In tests/bigtest.py

@pytest.fixture(scope='module')
def auth_headers(test_app, test_client):
    """
    Provides authentication headers for different user types.
    """
    headers = {'Content-Type': 'application/json'}
    
    # Login as teacher - save the session cookie properly
    teacher_response = test_client.post('/api/login', json={
        'email': 'teacher_test@example.com',
        'password': 'testpassword'
    })
    assert teacher_response.status_code == 200, f"Teacher login failed: {teacher_response.get_json()}"
    
    # Extract the session cookie correctly
    teacher_cookies = teacher_response.headers.getlist('Set-Cookie')
    teacher_cookie_header = '; '.join(teacher_cookies)
    
    # Login as student - same approach
    student_response = test_client.post('/api/login', json={
        'email': 'student_test@example.com',
        'password': 'testpassword'
    })
    assert student_response.status_code == 200, f"Student login failed: {student_response.get_json()}"
    student_cookies = student_response.headers.getlist('Set-Cookie')
    student_cookie_header = '; '.join(student_cookies)
    
    # Set up headers with cookies
    teacher_headers = {
        **headers,
        'Cookie': teacher_cookie_header
    }
    
    student_headers = {
        **headers,
        'Cookie': student_cookie_header
    }
    
    return {
        'teacher': teacher_headers,
        'student': student_headers
    }


@pytest.fixture(scope='module')
def test_course(test_app, test_client, auth_headers):
    """
    Create a test course for use in other tests.
    """
    with test_app.app_context():
        course_data = {
            'title': 'Test Course',
            'description': 'A comprehensive test course',
            'date': str(date.today() + timedelta(days=30)),
            'total_marks': 100,
            'difficulty_rating': 'medium'
        }
        
        course_response = test_client.post(
            '/api/courses/',
            json=course_data,
            headers=auth_headers['teacher']
        )
        
        assert course_response.status_code == 201, f"Course creation failed: {course_response.get_json()}"
        return json.loads(course_response.data)['data']


@pytest.fixture(scope='module')
def test_class(test_app, test_client, auth_headers):
    """
    Create a test class for use in other tests.
    """
    with test_app.app_context():
        class_data = {
            'name': 'Test Mathematics Class',
            'section_number': 'A'
        }
        
        class_response = test_client.post(
            '/api/classes/',
            json=class_data,
            headers=auth_headers['teacher']
        )
        
        assert class_response.status_code == 201, f"Class creation failed: {class_response.get_json()}"
        return json.loads(class_response.data)['data']


def test_authentication(test_app, test_client):
    """
    Test authentication endpoints.
    """
    # Test login with correct credentials
    login_response = test_client.post('/api/login', json={
        'email': 'teacher_test@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    
    # Convert response to JSON
    login_data = login_response.get_json()
    
    assert login_response.status_code == 200, f"Login failed: {login_data}"
    assert login_data.get('success') is True, "Login response missing success flag"
    assert login_data.get('user', {}).get('email') == 'teacher_test@example.com'
    
    # Test login with incorrect credentials
    login_fail_response = test_client.post('/api/login', json={
        'email': 'teacher_test@example.com',
        'password': 'wrongpassword'
    })
    assert login_fail_response.status_code == 401


def test_course_crud(test_app, test_client, auth_headers, test_course):
    """
    Test CRUD operations for courses.
    """
    # First verify the teacher's authentication status
    auth_check = test_client.get('/api/user', headers=auth_headers['teacher'])
    assert auth_check.status_code == 200, "Teacher authentication check failed"
    auth_data = json.loads(auth_check.data)
    assert auth_data['user']['role'] == 'teacher', f"User role is {auth_data['user']['role']}, expected 'teacher'"
    
    # Create course
    course_data = {
        'title': 'Test Course',
        'description': 'A comprehensive test course',
        'date': str(date.today() + timedelta(days=30)),
        'total_marks': 100,
        'difficulty_rating': 'medium'
    }
    
    create_response = test_client.post(
        '/api/courses/',
        json=course_data,
        headers=auth_headers['teacher']
    )
    
    # If creation fails, print detailed error information
    if create_response.status_code != 201:
        print(f"Course creation failed with status {create_response.status_code}")
        print(f"Response data: {create_response.get_json()}")
        print(f"Headers used: {auth_headers['teacher']}")
        
    assert create_response.status_code == 201, f"Course creation failed: {create_response.get_json()}"
    
    # Continue with rest of test...
    # Update course
    update_data = {
        'title': 'Updated Test Course',
        'description': 'An updated comprehensive test course'
    }
    update_response = test_client.put(
        f'/api/courses/{test_course["id"]}', 
        json=update_data, 
        headers=auth_headers['teacher']
    )
    assert update_response.status_code == 200
    updated_course = json.loads(update_response.data)['data']
    assert updated_course['title'] == 'Updated Test Course'
    
    # Get course details
    get_course_response = test_client.get(
        f'/api/courses/{test_course["id"]}', 
        headers=auth_headers['teacher']
    )
    assert get_course_response.status_code == 200
    
    # Delete course
    delete_response = test_client.delete(
        f'/api/courses/{test_course["id"]}', 
        headers=auth_headers['teacher']
    )
    assert delete_response.status_code == 200


def test_class_crud(test_app, test_client, auth_headers, test_class):
    """
    Test CRUD operations for classes.
    """
    # Update class
    update_data = {
        'name': 'Updated Test Mathematics Class',
        'section_number': 'B'
    }
    update_response = test_client.put(
        f'/api/classes/{test_class["id"]}', 
        json=update_data, 
        headers=auth_headers['teacher']
    )
    assert update_response.status_code == 200
    updated_class = json.loads(update_response.data)['data']
    assert updated_class['name'] == 'Updated Test Mathematics Class'
    
    # Get class details
    get_class_response = test_client.get(
        f'/api/classes/{test_class["id"]}', 
        headers=auth_headers['teacher']
    )
    assert get_class_response.status_code == 200
    
    # Attempt to add a student to the class
    with test_app.app_context():
        student = User.query.filter_by(role='student').first()
        student_data = {'student_id': student.id}
        
        add_student_response = test_client.post(
            f'/api/classes/{test_class["id"]}/students', 
            json=student_data, 
            headers=auth_headers['teacher']
        )
        assert add_student_response.status_code == 200
    
    # Delete class
    delete_response = test_client.delete(
        f'/api/classes/{test_class["id"]}', 
        headers=auth_headers['teacher']
    )
    assert delete_response.status_code == 200


def test_student_endpoints(test_app, test_client, auth_headers):
    """
    Test student-specific endpoints.
    """
    # Get student courses
    student_courses_response = test_client.get(
        '/api/students/courses', 
        headers=auth_headers['student']
    )
    assert student_courses_response.status_code == 200
    
    # Get student classes
    student_classes_response = test_client.get(
        '/api/students/classes', 
        headers=auth_headers['student']
    )
    assert student_classes_response.status_code == 200
    
    # Get student profile
    student_profile_response = test_client.get(
        '/api/students/profile', 
        headers=auth_headers['student']
    )
    assert student_profile_response.status_code == 200
    
    # Update student profile
    update_profile_data = {
        'name': 'Updated Student Name',
        'current_password': 'testpassword',
        'new_password': 'newpassword123'
    }
    update_profile_response = test_client.put(
        '/api/students/profile', 
        json=update_profile_data, 
        headers=auth_headers['student']
    )
    assert update_profile_response.status_code == 200
    
    # Verify profile was updated
    updated_profile = json.loads(update_profile_response.data)['data']
    assert updated_profile['name'] == 'Updated Student Name'


def test_authorization_checks(test_app, test_client, auth_headers):
    """
    Test various authorization scenarios.
    """
    # Attempt student to access teacher endpoints
    with test_app.app_context():
        # Try to create a course as a student
        course_data = {
            'title': 'Unauthorized Course',
            'description': 'Should not be created',
            'date': str(date.today() + timedelta(days=30)),
            'total_marks': 100,
            'difficulty_rating': 'medium'
        }
        
        # Create course as student (should fail)
        unauthorized_course_response = test_client.post(
            '/api/courses/', 
            json=course_data, 
            headers=auth_headers['student']
        )
        assert unauthorized_course_response.status_code == 403
        
        # Try to access teacher courses as student
        unauthorized_courses_response = test_client.get(
            '/api/courses/', 
            headers=auth_headers['student']
        )
        assert unauthorized_courses_response.status_code == 200  # Will return student's courses


def test_auth_status(test_client, auth_headers):
    """Verify the authentication status is working correctly."""
    # Test teacher authentication
    teacher_response = test_client.get('/api/isLoggedIn', headers=auth_headers['teacher'])
    teacher_data = json.loads(teacher_response.data)
    print(f"Teacher auth status response: {teacher_data}")
    
    assert teacher_response.status_code == 200, "Teacher auth check failed"
    assert teacher_data.get('isAuthenticated') is True, "Teacher not authenticated"
    assert teacher_data.get('user', {}).get('role') == 'teacher', "Teacher role incorrect"
    assert teacher_data.get('user', {}).get('is_teacher') is True, "Teacher is_teacher property incorrect"
    
    # Test student authentication
    student_response = test_client.get('/api/isLoggedIn', headers=auth_headers['student'])
    student_data = json.loads(student_response.data)
    print(f"Student auth status response: {student_data}")
    
    assert student_response.status_code == 200, "Student auth check failed"
    assert student_data.get('isAuthenticated') is True, "Student not authenticated"
    assert student_data.get('user', {}).get('role') == 'student', "Student role incorrect"
    assert not student_data.get('user', {}).get('is_teacher', True), "Student is_teacher property incorrect"
    
    # Test without authentication headers
    no_auth_response = test_client.get('/api/isLoggedIn')
    no_auth_data = json.loads(no_auth_response.data)
    print(f"No auth status response: {no_auth_data}")
    
    assert no_auth_response.status_code == 200, "No auth check failed"
    assert no_auth_data.get('isAuthenticated') is False, "Unauthenticated user shown as authenticated"
    assert no_auth_data.get('user') is None, "Unauthenticated user has user data"
