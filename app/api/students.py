"""
Students API for the Teacher Dashboard application.
Provides endpoints for student-specific operations and views.
"""
from flask import Blueprint, request, jsonify
from flask_smorest import Blueprint, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models.user import User
from app.models.course import Course
from app.models.class_model import Class
from app.models.associations import ClassStudent
from app.schemas.user import UserSchema, UserUpdateSchema
from app.schemas.course import CourseSchema
from app.schemas.class_schema import ClassSchema
from app.schemas.pagination import PaginatedResponseSchema
from app.models.associations import ClassCourse
from app.utils.security import student_required, resource_owner_required

students_blp = Blueprint(
    'students', 
    'students', 
    url_prefix='/api/students',
    description='Student-specific operations'
)


@students_blp.route('/courses', methods=['GET'])
@login_required
@student_required
def get_student_courses():
    """
    Get all courses the logged-in student is enrolled in.
    
    Query Parameters:
    - page: Page number for pagination (default: 1)
    - per_page: Number of items per page (default: 10, max: 100)
    - filters: Optional filtering parameters
    
    Returns:
        Paginated list of courses the student is enrolled in
    """
    # Ensure only students can access this endpoint
    if not current_user.is_student:
        abort(403, message="Only students can access this endpoint")
    
    # Parse pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    # Get enrolled class IDs
    enrolled_class_ids = [cs.class_id for cs in current_user.enrolled_classes]
    
    # Subquery to get unique course IDs from enrolled classes
    course_ids_subquery = db.session.query(
        func.distinct(ClassCourse.course_id)
    ).join(Class).filter(Class.id.in_(enrolled_class_ids)).subquery()
    
    # Base query for courses
    base_query = Course.query.filter(Course.id.in_(course_ids_subquery))
    
    # Optional: Apply additional filters if needed
    # (You can expand this based on CourseFiltersSchema similar to courses API)
    
    # Order by most recent courses first
    base_query = base_query.order_by(Course.date.desc())
    
    # Paginate
    paginated_courses = base_query.paginate(page=page, per_page=per_page)
    
    # Prepare response
    schema = CourseSchema(many=True)
    pagination_schema = PaginatedResponseSchema()
    
    return jsonify(pagination_schema.dump({
        'items': schema.dump(paginated_courses.items),
        'pagination': {
            'page': paginated_courses.page,
            'per_page': paginated_courses.per_page,
            'total_pages': paginated_courses.pages,
            'total_items': paginated_courses.total,
            'has_next': paginated_courses.has_next,
            'has_prev': paginated_courses.has_prev,
            'next_url': (request.base_url + f'?page={paginated_courses.next_num}&per_page={per_page}') 
                        if paginated_courses.has_next else None,
            'prev_url': (request.base_url + f'?page={paginated_courses.prev_num}&per_page={per_page}') 
                        if paginated_courses.has_prev else None
        }
    }))


@students_blp.route('/classes', methods=['GET'])
@login_required
@student_required
def get_student_classes():
    """
    Get all classes the logged-in student is enrolled in.
    
    Query Parameters:
    - page: Page number for pagination (default: 1)
    - per_page: Number of items per page (default: 10, max: 100)
    
    Returns:
        Paginated list of classes the student is enrolled in
    """
    # Ensure only students can access this endpoint
    if not current_user.is_student:
        abort(403, message="Only students can access this endpoint")
    
    # Parse pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    # Get enrolled class IDs
    enrolled_class_ids = [cs.class_id for cs in current_user.enrolled_classes]
    
    # Base query for classes
    base_query = Class.query.filter(Class.id.in_(enrolled_class_ids))
    
    # Order by class name
    base_query = base_query.order_by(Class.name)
    
    # Paginate
    paginated_classes = base_query.paginate(page=page, per_page=per_page)
    
    # Prepare response
    schema = ClassSchema(many=True)
    pagination_schema = PaginatedResponseSchema()
    
    return jsonify(pagination_schema.dump({
        'items': schema.dump(paginated_classes.items),
        'pagination': {
            'page': paginated_classes.page,
            'per_page': paginated_classes.per_page,
            'total_pages': paginated_classes.pages,
            'total_items': paginated_classes.total,
            'has_next': paginated_classes.has_next,
            'has_prev': paginated_classes.has_prev,
            'next_url': (request.base_url + f'?page={paginated_classes.next_num}&per_page={per_page}') 
                        if paginated_classes.has_next else None,
            'prev_url': (request.base_url + f'?page={paginated_classes.prev_num}&per_page={per_page}') 
                        if paginated_classes.has_prev else None
        }
    }))


@students_blp.route('/profile', methods=['GET'])
@login_required
@student_required
def get_student_profile():
    """
    Get the profile details of the logged-in student.
    
    Returns:
        Student profile information including enrolled classes and courses
    """
    # Ensure only students can access this endpoint
    if not current_user.is_student:
        abort(403, message="Only students can access this endpoint")
    
    # Prepare student details
    student_schema = UserSchema()
    course_schema = CourseSchema(many=True)
    class_schema = ClassSchema(many=True)
    
    # Get enrolled courses and classes
    enrolled_courses = current_user.get_enrolled_courses()
    enrolled_classes = [cs.class_ for cs in current_user.enrolled_classes]
    
    # Prepare response
    return jsonify({
        "status": "success",
        "data": {
            "profile": student_schema.dump(current_user),
            "enrolled_courses": course_schema.dump(enrolled_courses),
            "enrolled_classes": class_schema.dump(enrolled_classes)
        }
    })


@students_blp.route('/profile', methods=['PUT'])
@login_required
@student_required
def update_student_profile():
    """
    Update the profile of the logged-in student.
    
    Returns:
        Updated student profile information
    """
    # Validate request data
    schema = UserUpdateSchema()
    try:
        data = schema.load(request.json)
    except Exception as e:
        abort(400, message=str(e))
    
    # Check if current password is provided for password change
    if 'new_password' in data:
        # Verify current password
        if not current_user.check_password(data.get('current_password', '')):
            abort(400, message="Current password is incorrect")
        
        # Set new password
        current_user.set_password(data['new_password'])
    
    # Update other profile fields
    if 'email' in data:
        # Check if email is already in use
        existing_user = User.query.filter(
            User.email == data['email'], 
            User.id != current_user.id
        ).first()
        
        if existing_user:
            abort(409, message="Email is already in use")
        
        current_user.email = data['email']
    
    if 'name' in data:
        current_user.name = data['name']
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, message=f"Error updating profile: {str(e)}")
    
    # Prepare response
    schema = UserSchema()
    return jsonify({
        "status": "success",
        "message": "Profile updated successfully",
        "data": schema.dump(current_user)
    })