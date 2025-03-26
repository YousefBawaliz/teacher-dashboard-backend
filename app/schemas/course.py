"""
Course related schemas for the Teacher Dashboard application.
"""
from marshmallow import Schema, fields, validate, validates, ValidationError
import re
from datetime import datetime

class CourseRequestSchema(Schema):
    """Schema for course creation and update requests."""
    title = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    description = fields.Str(required=True)
    date = fields.Date(required=True)
    total_marks = fields.Int(required=True, validate=validate.Range(min=1, max=1000))
    difficulty_rating = fields.Str(required=True, validate=validate.OneOf(['easy', 'medium', 'hard', 'advanced']))
    
    @validates('title')
    def validate_title(self, value):
        """Validate course title."""
        if not value.strip():
            raise ValidationError('Course title cannot be empty.')
    
    @validates('description')
    def validate_description(self, value):
        """Validate course description."""
        if not value.strip():
            raise ValidationError('Course description cannot be empty.')
    
    @validates('date')
    def validate_date(self, value):
        """Validate that the date is not in the past."""
        if value < datetime.now().date():
            raise ValidationError('Course date cannot be in the past.')


class CourseSchema(Schema):
    """Schema for course serialization."""
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    description = fields.Str(required=True)
    date = fields.Date(required=True)
    total_marks = fields.Int(required=True)
    difficulty_rating = fields.Str(required=True)
    teacher_id = fields.Int(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class CourseFiltersSchema(Schema):
    """Schema for filtering courses."""
    title = fields.Str()
    difficulty = fields.Str(validate=validate.OneOf(['easy', 'medium', 'hard', 'advanced']))
    dateFrom = fields.Date()
    dateTo = fields.Date()
    
    @validates('dateFrom')
    def validate_date_from(self, value):
        """Validate dateFrom format."""
        if value and value > datetime.now().date():
            raise ValidationError('dateFrom cannot be in the future.')
    
    @validates('dateTo')
    def validate_date_to(self, value):
        """Validate dateTo format."""
        if value and value < datetime.now().date():
            raise ValidationError('dateTo cannot be in the past.')