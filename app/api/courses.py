"""
Courses API for the Teacher Dashboard application.
Provides endpoints for managing courses created by teachers.
"""
from flask import Blueprint, request, jsonify, g
from flask_smorest import Blueprint, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models.course import Course
from app.models.class_model import Class
from app.models.associations import ClassCourse
from app.schemas.course import (
    CourseSchema, 
    CourseRequestSchema, 
    CourseFiltersSchema
)
from app.schemas.pagination import PaginatedResponseSchema
from app.utils.security import teacher_required, resource_owner_required

courses_blp = Blueprint(
    'courses', 
    'courses', 
    url_prefix='/api/courses',
    description='Course management operations'
)


@courses_blp.route('/', methods=['GET'])
@login_required
def get_courses():
    """
    Get courses for the current user.
    
    For teachers: Returns all courses they've created
    For students: Returns courses they're enrolled in
    
    Query Parameters:
    - page: Page number for pagination (default: 1)
    - per_page: Number of items per page (default: 10, max: 100)
    - filters: Optional filtering parameters
    
    Returns:
        Paginated list of courses
    """
    # Parse pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    # Parse filters
    filter_schema = CourseFiltersSchema()
    try:
        filters = filter_schema.load(request.args) if request.args else {}
    except Exception as e:
        abort(400, message=str(e))
    
    # Base query depends on user role
    if current_user.is_teacher:
        # For teachers, get their own courses
        base_query = Course.query.filter_by(teacher_id=current_user.id)
    else:
        # For students, get courses from their enrolled classes
        enrolled_class_ids = [cs.class_id for cs in current_user.enrolled_classes]
        
        # Subquery to get course IDs from enrolled classes
        course_ids_subquery = db.session.query(
            db.func.distinct(ClassCourse.course_id)
        ).join(Class).filter(Class.id.in_(enrolled_class_ids)).subquery()
        
        base_query = Course.query.filter(Course.id.in_(course_ids_subquery))
    
    # Apply filters
    if filters.get('title'):
        base_query = base_query.filter(
            func.lower(Course.title).contains(func.lower(filters['title']))
        )
    
    if filters.get('difficulty'):
        base_query = base_query.filter(Course.difficulty_rating == filters['difficulty'])
    
    if filters.get('dateFrom'):
        base_query = base_query.filter(Course.date >= filters['dateFrom'])
    
    if filters.get('dateTo'):
        base_query = base_query.filter(Course.date <= filters['dateTo'])
    
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


@courses_blp.route('/<int:course_id>', methods=['GET'])
@login_required
def get_course_by_id(course_id):
    """
    Get detailed information about a specific course.
    
    For teachers: Any course they've created
    For students: Courses from their enrolled classes
    
    Args:
        course_id: ID of the course to retrieve
        
    Returns:
        Course details including assigned classes
    """
    course = Course.query.get_or_404(course_id)
    
    # Authorization checks
    if current_user.is_teacher:
        # Teacher can only view their own courses
        if course.teacher_id != current_user.id:
            abort(403, message="You can only view your own courses")
    else:
        # Student can only view courses from their enrolled classes
        enrolled_class_ids = [cs.class_id for cs in current_user.enrolled_classes]
        
        # Check if course is in any of the student's enrolled classes
        assigned_class_ids = [c.id for c in course.assigned_classes]
        if not set(enrolled_class_ids) & set(assigned_class_ids):
            abort(403, message="You are not enrolled in a class with this course")
    
    # Serialize the course with related classes
    schema = CourseSchema()
    result = schema.dump(course)
    
    # Add assigned classes to the response
    result['assigned_classes'] = [
        {'id': c.id, 'name': c.name, 'section_number': c.section_number} 
        for c in course.assigned_classes
    ]
    
    return jsonify({
        "status": "success",
        "data": result
    })


@courses_blp.route('/', methods=['POST'])
@login_required
@teacher_required
def create_course():
    """
    Create a new course (teacher only).
    
    Returns:
        The created course object
    """
    # Validate request data
    schema = CourseRequestSchema()
    try:
        data = schema.load(request.json)
    except Exception as e:
        abort(400, message=str(e))
    
    # Create the course with the current teacher as owner
    new_course = Course(
        title=data['title'],
        description=data['description'],
        date=data['date'],
        total_marks=data['total_marks'],
        difficulty_rating=data['difficulty_rating'],
        teacher_id=current_user.id
    )
    
    # Add to database
    db.session.add(new_course)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, message=f"Error creating course: {str(e)}")
    
    return jsonify({
        "status": "success",
        "message": "Course created successfully",
        "data": CourseSchema().dump(new_course)
    }), 201


@courses_blp.route('/<int:course_id>', methods=['PUT'])
@login_required
@teacher_required
@resource_owner_required(Course, owner_field='teacher_id')
def update_course(course_id):
    """
    Update an existing course (teacher only, must be course owner).
    
    Args:
        course_id: ID of the course to update
        
    Returns:
        The updated course object
    """
    # Course is retrieved by the resource_owner_required decorator and stored in g.resource
    course = g.resource
    
    # Validate request data
    schema = CourseRequestSchema(partial=True)
    try:
        data = schema.load(request.json)
    except Exception as e:
        abort(400, message=str(e))
    
    # Update course fields
    for key, value in data.items():
        setattr(course, key, value)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, message=f"Error updating course: {str(e)}")
    
    return jsonify({
        "status": "success",
        "message": "Course updated successfully",
        "data": CourseSchema().dump(course)
    })


@courses_blp.route('/<int:course_id>', methods=['DELETE'])
@login_required
@teacher_required
@resource_owner_required(Course, owner_field='teacher_id')
def delete_course(course_id):
    """
    Delete a course (teacher only, must be course owner).
    
    Args:
        course_id: ID of the course to delete
        
    Returns:
        Success message
    """
    # Course is retrieved by the resource_owner_required decorator and stored in g.resource
    course = g.resource
    
    # Delete the course (cascade will handle association tables)
    db.session.delete(course)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, message=f"Error deleting course: {str(e)}")
    
    return jsonify({
        "status": "success",
        "message": f"Course '{course.title}' deleted successfully"
    })
