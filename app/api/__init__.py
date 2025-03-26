"""
API package initialization.
Import all blueprints to make them available when importing from app.api.
"""

from app.api.auth import auth_blp
from app.api.classes import classes_blp
from app.api.courses import courses_blp
from app.api.students import students_blp