"""
Class related schemas for the Teacher Dashboard application.
"""
from marshmallow import Schema, fields, validate, validates, ValidationError
from app.schemas.user import UserSchema
from app.schemas.course import CourseSchema

class ClassCreateSchema(Schema):
    """Schema for class creation requests."""
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    section_number = fields.Str(required=True, validate=validate.Length(min=1, max=20))


class ClassUpdateSchema(Schema):
    """Schema for class update requests."""
    name = fields.Str(validate=validate.Length(min=2, max=100))
    section_number = fields.Str(validate=validate.Length(min=1, max=20))


class ClassCourseOperationSchema(Schema):
    """Schema for adding/removing a course to/from a class."""
    class_id = fields.Int(required=True)
    course_id = fields.Int(required=True)


class ClassStudentOperationSchema(Schema):
    """Schema for adding/removing a student to/from a class."""
    class_id = fields.Int(required=True)
    student_id = fields.Int(required=True)


class ClassSchema(Schema):
    """Schema for class serialization."""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    section_number = fields.Str(required=True)
    teacher_id = fields.Int(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    # Nested relationships - only included when explicitly requested
    teacher = fields.Nested(UserSchema, exclude=('password',), dump_only=True)
    students = fields.List(fields.Nested(UserSchema, exclude=('password',)), dump_only=True)
    courses = fields.List(fields.Nested(CourseSchema), dump_only=True)
    
    @validates('name')
    def validate_name(self, value):
        """Validate class name."""
        if not value.strip():
            raise ValidationError('Class name cannot be empty.')
    
    @validates('section_number')
    def validate_section(self, value):
        """Validate section number."""
        if not value.strip():
            raise ValidationError('Section number cannot be empty.')