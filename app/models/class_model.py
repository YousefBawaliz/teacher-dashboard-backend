"""
Class model for the Teacher Dashboard application.
Represents school classes with enrolled students and assigned courses.
"""
from datetime import datetime
from app import db

class Class(db.Model):
    """
    Class model representing a school class.
    Classes have a teacher, enrolled students, and assigned courses.
    """
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    section_number = db.Column(db.String(20), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    teacher = db.relationship('User', back_populates='teaching_classes')
    students = db.relationship('ClassStudent', back_populates='class_')
    course_associations = db.relationship('ClassCourse', back_populates='class_', cascade='all, delete-orphan')
    
    def __init__(self, name, section_number, teacher_id):
        self.name = name
        self.section_number = section_number
        self.teacher_id = teacher_id
    
    @property
    def courses(self):
        """Get all courses assigned to this class."""
        from app.models.course import Course
        course_ids = [cc.course_id for cc in self.course_associations]
        return Course.query.filter(Course.id.in_(course_ids)).all() if course_ids else []
    
    @property
    def enrolled_students(self):
        """Get all students enrolled in this class."""
        from app.models.user import User
        student_ids = [cs.student_id for cs in self.students]
        return User.query.filter(User.id.in_(student_ids)).all() if student_ids else []
    
    def add_course(self, course_id):
        """Add a course to this class."""
        from app.models.associations import ClassCourse
        
        # Check if course is already assigned
        existing = ClassCourse.query.filter_by(
            class_id=self.id, course_id=course_id
        ).first()
        
        if not existing:
            association = ClassCourse(class_id=self.id, course_id=course_id)
            db.session.add(association)
            return True
        return False
    
    def remove_course(self, course_id):
        """Remove a course from this class."""
        from app.models.associations import ClassCourse
        
        association = ClassCourse.query.filter_by(
            class_id=self.id, course_id=course_id
        ).first()
        
        if association:
            db.session.delete(association)
            return True
        return False
    
    def add_student(self, student_id):
        """Enroll a student in this class."""
        from app.models.associations import ClassStudent
        
        # Check if student is already enrolled
        existing = ClassStudent.query.filter_by(
            class_id=self.id, student_id=student_id
        ).first()
        
        if not existing:
            association = ClassStudent(class_id=self.id, student_id=student_id)
            db.session.add(association)
            return True
        return False
    
    def remove_student(self, student_id):
        """Remove a student from this class."""
        from app.models.associations import ClassStudent
        
        association = ClassStudent.query.filter_by(
            class_id=self.id, student_id=student_id
        ).first()
        
        if association:
            db.session.delete(association)
            return True
        return False
    
    def to_dict(self, include_relationships=False):
        """Convert class object to dictionary for API responses."""
        data = {
            'id': self.id,
            'name': self.name,
            'section_number': self.section_number,
            'teacher_id': self.teacher_id
        }
        
        if include_relationships:
            data['teacher'] = self.teacher.to_dict(include_email=False) if self.teacher else None
            data['students'] = [s.to_dict(include_email=False) for s in self.enrolled_students]
            data['courses'] = [c.to_dict() for c in self.courses]
        
        return data
    
    def __repr__(self):
        return f'<Class {self.id}: {self.name} (Section {self.section_number})>'