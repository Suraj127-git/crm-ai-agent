from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from services.crm.crm_client import CRMClient
from chatbot.agents.crewai_agent import create_course_recommendation_crew
from models.user import User
from models.course import Course

class CourseRecommender:
    """Service for AI-powered course recommendations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.crm_client = CRMClient()
    
    def get_user_profile(self, user_id: int) -> Dict:
        """Get user profile information from both database and CRM"""
        # Get user from database
        db_user = self.db.query(User).filter(User.id == user_id).first()
        
        if not db_user:
            return None
        
        # Try to get additional user information from CRM
        try:
            crm_user = self.crm_client.get_user(user_id)
            # Merge CRM user data with database user
            user_profile = {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "is_active": db_user.is_active,
                # Add additional fields from CRM if available
                "interests": crm_user.get("interests", []),
                "education_level": crm_user.get("education_level"),
                "career_goals": crm_user.get("career_goals", []),
                "enrolled_courses": crm_user.get("enrolled_courses", []),
                "completed_courses": crm_user.get("completed_courses", [])
            }
        except Exception:
            # If CRM data is unavailable, use only database data
            user_profile = {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "is_active": db_user.is_active,
                "interests": [],
                "education_level": None,
                "career_goals": [],
                "enrolled_courses": [],
                "completed_courses": []
            }
        
        return user_profile
    
    def get_available_courses(self, category: Optional[str] = None, difficulty: Optional[str] = None) -> List[Dict]:
        """Get available courses from both database and CRM"""
        # Query courses from database
        query = self.db.query(Course)
        
        if category:
            query = query.filter(Course.category == category)
        
        if difficulty:
            query = query.filter(Course.difficulty_level == difficulty)
        
        db_courses = query.all()
        
        # Convert to list of dictionaries
        courses = [{
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "difficulty_level": course.difficulty_level,
            "duration_hours": course.duration_hours,
            "price": course.price,
            "instructor_id": course.instructor_id
        } for course in db_courses]
        
        # Try to get additional courses from CRM
        try:
            crm_courses = self.crm_client.get_courses(
                category=category,
                difficulty=difficulty
            ).get("data", [])
            
            # Merge CRM courses with database courses (avoid duplicates)
            db_course_ids = set(course["id"] for course in courses)
            
            for crm_course in crm_courses:
                if crm_course["id"] not in db_course_ids:
                    courses.append(crm_course)
        except Exception:
            # If CRM data is unavailable, use only database courses
            pass
        
        return courses
    
    def recommend_courses(self, user_id: int, query: str) -> Dict:
        """Recommend courses based on user profile and query"""
        # Get user profile
        user_profile = self.get_user_profile(user_id)
        
        if not user_profile:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Get available courses
        available_courses = self.get_available_courses()
        
        # Create a crew for course recommendations
        crew = create_course_recommendation_crew(
            user_query=query,
            user_profile=user_profile,
            available_courses=available_courses
        )
        
        # Execute the crew's tasks to get recommendations
        result = crew.kickoff()
        
        return {
            "recommendations": result,
            "user_profile": user_profile,
            "query": query
        }