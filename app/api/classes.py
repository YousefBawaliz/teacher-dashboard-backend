"""
Classes API for the Teacher Dashboard application.
Provides endpoints for managing classes, their students, and assigned courses.
"""
from flask import Blueprint, request, jsonify, g
from flask_smorest import Blueprint, abort
from flask_login import login_required, current_user
from app import db
from app.models.class_model import Class
from app.models.course import Course
from app.models.user import User
from app.models.associations import ClassCourse, ClassStudent
from app.schemas.class_schema import (
    ClassSchema, ClassCreateSchema, ClassUpdateSchema,
    ClassCourseOperationSchema, ClassStudentOperationSchema
)
from app.utils.security import teacher_required, resource_owner_required

classes_blp = Blueprint(
    'classes', 
    'classes', 
    url_prefix='/api/classes',
    description='Class management operations'
)


@classes_blp.route('/', methods=['GET'])
@login_required
def get_classes():
    """
    Get all classes for the current user based on their role.
    
    For teachers: Returns classes they are teaching
    For students: Returns classes they are enrolled in
    
    Returns:
        List of classes with basic information
    """
    if current_user.is_teacher:
        # Get classes taught by the teacher
        classes = Class.query.filter_by(teacher_id=current_user.id).all()
    else:
        # Get classes the student is enrolled in
        enrolled_class_ids = [cs.class_id for cs in current_user.enrolled_classes]
        classes = Class.query.filter(Class.id.in_(enrolled_class_ids)).all() if enrolled_class_ids else []
    
    # Serialize the classes
    schema = ClassSchema(many=True)
    result = schema.dump(classes)
    
    return jsonify({
        "status": "success",
        "data": result
    })


@classes_blp.route('/<int:class_id>', methods=['GET'])
@login_required
def get_class_by_id(class_id):
    """
    Get detailed information about a specific class.
    
    For teachers: Only their own classes
    For students: Only classes they are enrolled in
    
    Args:
        class_id: ID of the class to retrieve
        
    Returns:
        Class details including enrolled students and assigned courses
    """
    class_item = Class.query.get_or_404(class_id)
    
    # Check access permissions
    if current_user.is_teacher and class_item.teacher_id != current_user.id:
        abort(403, message="You can only view your own classes")
    
    if current_user.is_student:
        # Check if student is enrolled in this class
        is_enrolled = ClassStudent.query.filter_by(
            class_id=class_id, student_id=current_user.id
        ).first() is not None
        
        if not is_enrolled:
            abort(403, message="You are not enrolled in this class")
    
    # Serialize the class with related entities
    schema = ClassSchema()
    result = schema.dump(class_item)
    
    # Add students and courses
    result['students'] = [s.to_dict(include_email=False) for s in class_item.enrolled_students]
    result['courses'] = [c.to_dict() for c in class_item.courses]
    
    return jsonify({
        "status": "success",
        "data": result
    })


@classes_blp.route('/', methods=['POST'])
@login_required
@teacher_required
def create_class():
    """
    Create a new class (teacher only).
    
    Returns:
        The created class object
    """
    # Validate request data
    schema = ClassCreateSchema()
    try:
        data = schema.load(request.json)
    except Exception as e:
        abort(400, message=str(e))
    
    # Create the class with the current teacher as owner
    new_class = Class(
        name=data['name'],
        section_number=data['section_number'],
        teacher_id=current_user.id
    )
    
    # Add to database
    db.session.add(new_class)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, message=f"Error creating class: {str(e)}")
    
    return jsonify({
        "status": "success",
        "message": "Class created successfully",
        "data": ClassSchema().dump(new_class)
    }), 201


@classes_blp.route('/<int:class_id>', methods=['PUT'])
@login_required
@teacher_required
@resource_owner_required(Class, owner_field='teacher_id')
def update_class(class_id):
    """
    Update an existing class (teacher only, must be owner).
    
    Args:
        class_id: ID of the class to update
        
    Returns:
        The updated class object
    """
    # Class is retrieved by the resource_owner_required decorator and stored in g.resource
    class_item = g.resource
    
    # Validate request data
    schema = ClassUpdateSchema()
    try:
        data = schema.load(request.json)
    except Exception as e:
        abort(400, message=str(e))
    
    # Update class fields
    if 'name' in data:
        class_item.name = data['name']
    
    if 'section_number' in data:
        class_item.section_number = data['section_number']
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, message=f"Error updating class: {str(e)}")
    
    return jsonify({
        "status": "success",
        "message": "Class updated successfully",
        "data": ClassSchema().dump(class_item)
    })


@classes_blp.route('/<int:class_id>', methods=['DELETE'])
@login_required
@teacher_required
@resource_owner_required(Class, owner_field='teacher_id')
def delete_class(class_id):
    """
    Delete a class (teacher only, must be owner).
    
    Args:
        class_id: ID of the class to delete
        
    Returns:
        Success message
    """
    # Class is retrieved by the resource_owner_required decorator and stored in g.resource
    class_item = g.resource
    
    # Delete the class (cascade will handle association tables)
    db.session.delete(class_item)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, message=f"Error deleting class: {str(e)}")
    
    return jsonify({
        "status": "success",
        "message": f"Class '{class_item.name}' deleted successfully"
    })


@classes_blp.route('/<int:class_id>/students', methods=['GET'])
@login_required
def get_class_students(class_id):
    """
    Get all students enrolled in a specific class.
    
    Args:
        class_id: ID of the class
        
    Returns:
        List of students enrolled in the class
    """
    class_item = Class.query.get_or_404(class_id)
    
    # Check access permissions
    if current_user.is_teacher and class_item.teacher_id != current_user.id:
        abort(403, message="You can only view your own classes")
    
    if current_user.is_student:
        # Check if student is enrolled in this class
        is_enrolled = ClassStudent.query.filter_by(
            class_id=class_id, student_id=current_user.id
        ).first() is not None
        
        if not is_enrolled:
            abort(403, message="You are not enrolled in this class")
    
    # Get students enrolled in the class
    students = class_item.enrolled_students
    
    return jsonify({
        "status": "success",
        "data": [s.to_dict(include_email=False) for s in students]
    })


@classes_blp.route('/<int:class_id>/courses', methods=['GET'])
@login_required
def get_class_courses(class_id):
    """
    Get all courses assigned to a specific class.
    
    Args:
        class_id: ID of the class
        
    Returns:
        List of courses assigned to the class
    """
    class_item = Class.query.get_or_404(class_id)
    
    # Check access permissions
    if current_user.is_teacher and class_item.teacher_id != current_user.id:
        abort(403, message="You can only view your own classes")
    
    if current_user.is_student:
        # Check if student is enrolled in this class
        is_enrolled = ClassStudent.query.filter_by(
            class_id=class_id, student_id=current_user.id
        ).first() is not None
        
        if not is_enrolled:
            abort(403, message="You are not enrolled in this class")
    
    # Get courses assigned to the class
    courses = class_item.courses
    
    return jsonify({
        "status": "success",
        "data": [c.to_dict() for c in courses]
    })


@classes_blp.route('/<int:class_id>/courses', methods=['POST'])
@login_required
@teacher_required
@resource_owner_required(Class, owner_field='teacher_id')
def add_course_to_class(class_id):
    """
    Add a course to a class (teacher only, must be class owner).
    
    Args:
        class_id: ID of the class
        
    Returns:
        Success message
    """
    # Class is retrieved by the resource_owner_required decorator and stored in g.resource
    class_item = g.resource
    
    # Validate request data
    schema = ClassCourseOperationSchema()
    try:
        data = schema.load(request.json)
    except Exception as e:
        abort(400, message=str(e))
    
    # Ensure course exists
    course_id = data['course_id']
    course = Course.query.get(course_id)
    if not course:
        abort(404, message=f"Course with ID {course_id} not found")
    
    # Add the course to the class
    success = class_item.add_course(course_id)
    
    if not success:
        return jsonify({
            "status": "error",
            "message": "Course is already assigned to this class"
        }), 409
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, message=f"Error adding course to class: {str(e)}")
    
    return jsonify({
        "status": "success",
        "message": f"Course '{course.title}' added to class successfully"
    })


@classes_blp.route('/<int:class_id>/courses/<int:course_id>', methods=['DELETE'])
@login_required
@teacher_required
@resource_owner_required(Class, owner_field='teacher_id')
def remove_course_from_class(class_id, course_id):
    """
    Remove a course from a class (teacher only, must be class owner).
    
    Args:
        class_id: ID of the class
        course_id: ID of the course to remove
        
    Returns:
        Success message
    """
    # Class is retrieved by the resource_owner_required decorator and stored in g.resource
    class_item = g.resource
    
    # Ensure course exists
    course = Course.query.get(course_id)
    if not course:
        abort(404, message=f"Course with ID {course_id} not found")
    
    # Remove the course from the class
    success = class_item.remove_course(course_id)
    
    if not success:
        return jsonify({
            "status": "error",
            "message": "Course is not assigned to this class"
        }), 404
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, message=f"Error removing course from class: {str(e)}")
    
    return jsonify({
        "status": "success",
        "message": f"Course '{course.title}' removed from class successfully"
    })


@classes_blp.route('/<int:class_id>/students', methods=['POST'])
@login_required
@teacher_required
@resource_owner_required(Class, owner_field='teacher_id')
def add_student_to_class(class_id):
    """
    Add a student to a class (teacher only, must be class owner).
    
    Args:
        class_id: ID of the class
        
    Returns:
        Success message
    """
    # Class is retrieved by the resource_owner_required decorator and stored in g.resource
    class_item = g.resource
    
    # Validate request data
    schema = ClassStudentOperationSchema()
    try:
        data = schema.load(request.json)
    except Exception as e:
        abort(400, message=str(e))
    
    # Ensure student exists and is a student
    student_id = data['student_id']
    student = User.query.get(student_id)
    if not student:
        abort(404, message=f"User with ID {student_id} not found")
    
    if student.role != 'student':
        abort(400, message="Only students can be enrolled in classes")
    
    # Add the student to the class
    success = class_item.add_student(student_id)
    
    if not success:
        return jsonify({
            "status": "error",
            "message": "Student is already enrolled in this class"
        }), 409
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, message=f"Error adding student to class: {str(e)}")
    
    return jsonify({
        "status": "success",
        "message": f"Student '{student.name}' enrolled in class successfully"
    })


@classes_blp.route('/<int:class_id>/students/<int:student_id>', methods=['DELETE'])
@login_required
@teacher_required
@resource_owner_required(Class, owner_field='teacher_id')
def remove_student_from_class(class_id, student_id):
    """
    Remove a student from a class (teacher only, must be class owner).
    
    Args:
        class_id: ID of the class
        student_id: ID of the student to remove
        
    Returns:
        Success message
    """
    # Class is retrieved by the resource_owner_required decorator and stored in g.resource
    class_item = g.resource
    
    # Ensure student exists
    student = User.query.get(student_id)
    if not student:
        abort(404, message=f"User with ID {student_id} not found")
    
    # Remove the student from the class
    success = class_item.remove_student(student_id)
    
    if not success:
        return jsonify({
            "status": "error",
            "message": "Student is not enrolled in this class"
        }), 404
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, message=f"Error removing student from class: {str(e)}")
    
    return jsonify({
        "status": "success",
        "message": f"Student '{student.name}' removed from class successfully"
    })


@classes_blp.route('/<int:class_id>/students/bulk', methods=['POST'])
@login_required
@teacher_required
@resource_owner_required(Class, owner_field='teacher_id')
def bulk_add_students(class_id):
    """
    Add multiple students to a class in a single operation (teacher only, must be class owner).
    
    Args:
        class_id: ID of the class
        
    Expected JSON body:
        {
            "student_ids": [1, 2, 3, ...]
        }
        
    Returns:
        Success message with details of added students
    """
    # Class is retrieved by the resource_owner_required decorator and stored in g.resource
    class_item = g.resource
    
    # Validate request data
    if not request.is_json:
        abort(400, message="Request must be JSON")
    
    data = request.get_json()
    if not isinstance(data.get('student_ids', []), list):
        abort(400, message="student_ids must be a list of integers")
    
    student_ids = data['student_ids']
    if not student_ids:
        abort(400, message="No student IDs provided")
    
    # Track results
    results = {
        'success': [],
        'already_enrolled': [],
        'not_found': [],
        'not_students': []
    }
    
    for student_id in student_ids:
        # Ensure student exists and is a student
        student = User.query.get(student_id)
        if not student:
            results['not_found'].append(student_id)
            continue
            
        if student.role != 'student':
            results['not_students'].append(student_id)
            continue
        
        # Try to add the student
        if class_item.add_student(student_id):
            results['success'].append({
                'id': student_id,
                'name': student.name
            })
        else:
            results['already_enrolled'].append({
                'id': student_id,
                'name': student.name
            })
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, message=f"Error adding students to class: {str(e)}")
    
    # Prepare response message
    message = []
    if results['success']:
        message.append(f"Successfully added {len(results['success'])} students")
    if results['already_enrolled']:
        message.append(f"{len(results['already_enrolled'])} students were already enrolled")
    if results['not_found']:
        message.append(f"{len(results['not_found'])} student IDs not found")
    if results['not_students']:
        message.append(f"{len(results['not_students'])} users were not students")
    
    return jsonify({
        "status": "success",
        "message": ". ".join(message),
        "details": results
    })


@classes_blp.route('/<int:class_id>/students/bulk', methods=['DELETE'])
@login_required
@teacher_required
@resource_owner_required(Class, owner_field='teacher_id')
def bulk_remove_students(class_id):
    """
    Remove multiple students from a class in a single operation (teacher only, must be class owner).
    
    Args:
        class_id: ID of the class
        
    Expected JSON body:
        {
            "student_ids": [1, 2, 3, ...]
        }
        
    Returns:
        Success message with details of removed students
    """
    # Class is retrieved by the resource_owner_required decorator and stored in g.resource
    class_item = g.resource
    
    # Validate request data
    if not request.is_json:
        abort(400, message="Request must be JSON")
    
    data = request.get_json()
    if not isinstance(data.get('student_ids', []), list):
        abort(400, message="student_ids must be a list of integers")
    
    student_ids = data['student_ids']
    if not student_ids:
        abort(400, message="No student IDs provided")
    
    # Track results
    results = {
        'success': [],
        'not_enrolled': [],
        'not_found': []
    }
    
    for student_id in student_ids:
        # Ensure student exists
        student = User.query.get(student_id)
        if not student:
            results['not_found'].append(student_id)
            continue
        
        # Try to remove the student
        if class_item.remove_student(student_id):
            results['success'].append({
                'id': student_id,
                'name': student.name
            })
        else:
            results['not_enrolled'].append({
                'id': student_id,
                'name': student.name
            })
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, message=f"Error removing students from class: {str(e)}")
    
    # Prepare response message
    message = []
    if results['success']:
        message.append(f"Successfully removed {len(results['success'])} students")
    if results['not_enrolled']:
        message.append(f"{len(results['not_enrolled'])} students were not enrolled")
    if results['not_found']:
        message.append(f"{len(results['not_found'])} student IDs not found")
    
    return jsonify({
        "status": "success",
        "message": ". ".join(message),
        "details": results
    })