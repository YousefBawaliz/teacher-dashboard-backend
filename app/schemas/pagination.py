"""
Pagination schema for the Teacher Dashboard application.
Used for paginating API responses that return collections.
"""
from marshmallow import Schema, fields, validate, validates, ValidationError, post_dump

class PaginationSchema(Schema):
    """Schema for pagination metadata."""
    page = fields.Int(dump_only=True)
    per_page = fields.Int(dump_only=True)
    total_pages = fields.Int(dump_only=True)
    total_items = fields.Int(dump_only=True)
    has_next = fields.Bool(dump_only=True)
    has_prev = fields.Bool(dump_only=True)
    
    # Optional fields for navigation links
    next_url = fields.Str(dump_only=True)
    prev_url = fields.Str(dump_only=True)
    first_url = fields.Str(dump_only=True)
    last_url = fields.Str(dump_only=True)
    
    @post_dump
    def remove_none_values(self, data, **kwargs):
        """Remove None values from the output."""
        return {key: value for key, value in data.items() if value is not None}


class PaginatedResponseSchema(Schema):
    """
    Schema for paginated responses.
    This schema wraps around an items field which contains the actual data.
    """
    items = fields.List(fields.Dict(), required=True)
    pagination = fields.Nested(PaginationSchema, required=True)
    
    @post_dump
    def wrap_with_envelope(self, data, **kwargs):
        """Wrap the response in a standard format."""
        return {
            "status": "success",
            "data": data
        }