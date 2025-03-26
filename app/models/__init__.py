"""
Models package initialization.
Import all models to make them available when importing from app.models.
"""

from app.models.user import User
from app.models.class_model import Class
from app.models.course import Course
from app.models.associations import ClassCourse, ClassStudent