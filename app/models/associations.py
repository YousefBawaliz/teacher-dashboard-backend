"""
Association models for the Teacher Dashboard application.
Defines many-to-many relationships between classes, courses, and students.
"""
from datetime import datetime
from app import db

class ClassCourse(db.Model):
    """
    Association model for the many-to-many relationship between classes and courses.
    Represents a course assigned to a specific class.
    """
    __tablename__ = 'class_courses'
    
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add a unique constraint to prevent duplicates
    __table_args__ = (db.UniqueConstraint('class_id', 'course_id', name='uq_class_course'),)
    
    # Relationships
    class_ = db.relationship('Class', back_populates='course_associations')
    course = db.relationship('Course', back_populates='class_associations')
    
    def __init__(self, class_id, course_id):
        self.class_id = class_id
        self.course_id = course_id
    
    def __repr__(self):
        return f'<ClassCourse: Class {self.class_id} - Course {self.course_id}>'


class ClassStudent(db.Model):
    """
    Association model for the many-to-many relationship between classes and students.
    Represents a student enrolled in a specific class.
    """
    __tablename__ = 'class_students'
    
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrolled_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add a unique constraint to prevent duplicates
    __table_args__ = (db.UniqueConstraint('class_id', 'student_id', name='uq_class_student'),)
    
    # Relationships
    class_ = db.relationship('Class', back_populates='students')
    student = db.relationship('User', back_populates='enrolled_classes')
    
    def __init__(self, class_id, student_id):
        self.class_id = class_id
        self.student_id = student_id
    
    def __repr__(self):
        return f'<ClassStudent: Class {self.class_id} - Student {self.student_id}>'