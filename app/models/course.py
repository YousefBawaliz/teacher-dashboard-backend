"""
Course model for the Teacher Dashboard application.
Represents courses that can be assigned to classes.
"""
from datetime import datetime
from app import db

class Course(db.Model):
    """
    Course model representing an educational course.
    Courses are created by teachers and can be assigned to multiple classes.
    """
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    difficulty_rating = db.Column(db.String(20), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    teacher = db.relationship('User', back_populates='created_courses')
    class_associations = db.relationship('ClassCourse', back_populates='course', cascade='all, delete-orphan')
    
    def __init__(self, title, description, date, total_marks, difficulty_rating, teacher_id):
        self.title = title
        self.description = description
        self.date = date
        self.total_marks = total_marks
        self.difficulty_rating = difficulty_rating
        self.teacher_id = teacher_id
    
    @property
    def assigned_classes(self):
        """Get all classes this course is assigned to."""
        from app.models.class_model import Class
        class_ids = [cc.class_id for cc in self.class_associations]
        return Class.query.filter(Class.id.in_(class_ids)).all() if class_ids else []
    
    def is_valid_difficulty(self):
        """Validate that the difficulty rating is one of the allowed values."""
        valid_ratings = ['easy', 'medium', 'hard', 'advanced']
        return self.difficulty_rating in valid_ratings
    
    def to_dict(self):
        """Convert course object to dictionary for API responses."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'date': self.date.isoformat() if self.date else None,
            'total_marks': self.total_marks,
            'difficulty_rating': self.difficulty_rating,
            'teacher_id': self.teacher_id
        }
    
    def __repr__(self):
        return f'<Course {self.id}: {self.title}>'