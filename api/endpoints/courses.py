from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from db.utils.database import get_db
from models.course import Course
from models.user import User
from api.endpoints.auth import get_current_user

router = APIRouter()

# Pydantic models
class CourseBase(BaseModel):
    title: str
    description: str
    category: str
    difficulty_level: str
    duration_hours: float
    price: float

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int
    instructor_id: int
    
    class Config:
        from_attributes = True

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty_level: Optional[str] = None
    duration_hours: Optional[float] = None
    price: Optional[float] = None

# Endpoints
@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course: CourseCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_course = Course(
        **course.dict(),
        instructor_id=current_user.id
    )
    
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    
    return db_course

@router.get("/", response_model=List[CourseResponse])
def get_courses(
    skip: int = 0, 
    limit: int = 100,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Course)
    
    # Apply filters if provided
    if category:
        query = query.filter(Course.category == category)
    if difficulty:
        query = query.filter(Course.difficulty_level == difficulty)
    
    courses = query.offset(skip).limit(limit).all()
    return courses

@router.get("/{course_id}", response_model=CourseResponse)
def get_course_by_id(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.patch("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if db_course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if user is the instructor of the course
    if db_course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this course")
    
    # Update only provided fields
    update_data = course_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_course, key, value)
    
    db.commit()
    db.refresh(db_course)
    
    return db_course

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if db_course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if user is the instructor of the course
    if db_course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this course")
    
    db.delete(db_course)
    db.commit()
    
    return None

@router.get("/instructor/{instructor_id}", response_model=List[CourseResponse])
def get_instructor_courses(
    instructor_id: int,
    db: Session = Depends(get_db)
):
    courses = db.query(Course).filter(Course.instructor_id == instructor_id).all()
    return courses