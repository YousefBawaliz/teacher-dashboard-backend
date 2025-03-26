"""
User model for the Teacher Dashboard application.
Defines teacher and student user types with appropriate relationships.
"""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db

class User(db.Model, UserMixin):
    """
    User model representing both teachers and students.
    UserMixin provides Flask-Login compatibility.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations for teachers
    teaching_classes = db.relationship('Class', back_populates='teacher', lazy='dynamic')
    created_courses = db.relationship('Course', back_populates='teacher', lazy='dynamic')
    
    # Relations for students
    enrolled_classes = db.relationship('ClassStudent', back_populates='student', lazy='dynamic')
    
    def __init__(self, email, name, role, password=None):
        self.email = email
        self.name = name
        self.role = role
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify the user's password."""
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_teacher(self):
        """Check if the user is a teacher."""
        return self.role == 'teacher'
    
    @property
    def is_student(self):
        """Check if the user is a student."""
        return self.role == 'student'
    
    def get_enrolled_courses(self):
        """Get all courses that a student is enrolled in through their classes."""
        if not self.is_student:
            return []
            
        # Collect all classes the student is enrolled in
        enrolled_class_ids = [cs.class_id for cs in self.enrolled_classes]
        
        # Get all courses associated with these classes
        from app.models.associations import ClassCourse
        
        course_ids = db.session.query(ClassCourse.course_id) \
            .filter(ClassCourse.class_id.in_(enrolled_class_ids)) \
            .distinct().all()
            
        from app.models.course import Course
        
        return Course.query.filter(Course.id.in_([cid[0] for cid in course_ids])).all()
    
    def to_dict(self, include_email=True):
        """Convert user object to dictionary for API responses."""
        data = {
            'id': self.id,
            'name': self.name,
            'role': self.role
        }
        if include_email:
            data['email'] = self.email
        return data
    
    def __repr__(self):
        return f'<User {self.id}: {self.email} ({self.role})>'