"""
User related schemas for the Teacher Dashboard application.
"""
from marshmallow import Schema, fields, validate, validates, validates_schema, ValidationError
import re

class UserSchema(Schema):
    """Schema for user serialization and validation."""
    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    role = fields.Str(required=True, validate=validate.OneOf(['teacher', 'student']))
    
    # These fields are only used for user creation, not in responses
    password = fields.Str(load_only=True, required=False)
    
    # These fields are only in responses
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    @validates('email')
    def validate_email(self, value):
        """Custom validation for email addresses."""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValidationError('Invalid email format.')
    
    @validates('password')
    def validate_password(self, value):
        """Validate password strength."""
        if value and len(value) < 8:
            raise ValidationError('Password must be at least 8 characters.')


class LoginSchema(Schema):
    """Schema for login requests."""
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    remember = fields.Bool(missing=False)


class UserCreateSchema(Schema):
    """Schema for user creation requests."""
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    role = fields.Str(required=True, validate=validate.OneOf(['teacher', 'student']))
    
    @validates('email')
    def validate_email(self, value):
        """Custom validation for email addresses."""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValidationError('Invalid email format.')


class UserUpdateSchema(Schema):
    """Schema for user update requests."""
    email = fields.Email()
    name = fields.Str(validate=validate.Length(min=2, max=100))
    current_password = fields.Str()
    new_password = fields.Str(validate=validate.Length(min=8))
    
    @validates('email')
    def validate_email(self, value):
        """Custom validation for email addresses."""
        if value and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValidationError('Invalid email format.')
    
    @validates_schema
    def validate_password_change(self, data, **kwargs):
        """Validate that current password is provided when changing password."""
        if 'new_password' in data and 'current_password' not in data:
            raise ValidationError('Current password is required to set a new password.')
