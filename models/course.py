from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.utils.database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(Text)
    instructor_id = Column(Integer, ForeignKey("users.id"))
    category = Column(String(100))
    difficulty_level = Column(String(50))
    duration_hours = Column(Float)
    price = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    instructor = relationship("User", back_populates="courses")
    
    def __repr__(self):
        return f"<Course {self.title}>"