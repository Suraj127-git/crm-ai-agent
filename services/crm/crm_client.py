import requests
import os
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

class CRMClient:
    """Client for interacting with the Laravel CRM API"""
    
    def __init__(self):
        self.base_url = os.getenv("LARAVEL_CRM_BASE_URL")
        self.api_key = os.getenv("LARAVEL_CRM_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None):
        """Make a request to the Laravel CRM API"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params
            )
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Handle HTTP errors
            error_message = f"HTTP error occurred: {e}"
            if response.text:
                try:
                    error_data = response.json()
                    error_message = f"{error_message} - {error_data.get('message', '')}"
                except:
                    error_message = f"{error_message} - {response.text}"
            
            raise Exception(error_message)
        except requests.exceptions.RequestException as e:
            # Handle connection errors
            raise Exception(f"Request error occurred: {e}")
    
    # User-related methods
    def get_users(self, page: int = 1, per_page: int = 100) -> Dict:
        """Get users from the CRM"""
        params = {"page": page, "per_page": per_page}
        return self._make_request("GET", "users", params=params)
    
    def get_user(self, user_id: int) -> Dict:
        """Get a specific user from the CRM"""
        return self._make_request("GET", f"users/{user_id}")
    
    def create_user(self, user_data: Dict) -> Dict:
        """Create a new user in the CRM"""
        return self._make_request("POST", "users", data=user_data)
    
    def update_user(self, user_id: int, user_data: Dict) -> Dict:
        """Update a user in the CRM"""
        return self._make_request("PUT", f"users/{user_id}", data=user_data)
    
    # Course-related methods
    def get_courses(self, 
                    page: int = 1, 
                    per_page: int = 100,
                    category: Optional[str] = None,
                    difficulty: Optional[str] = None) -> Dict:
        """Get courses from the CRM"""
        params = {
            "page": page, 
            "per_page": per_page
        }
        
        if category:
            params["category"] = category
        
        if difficulty:
            params["difficulty"] = difficulty
        
        return self._make_request("GET", "courses", params=params)
    
    def get_course(self, course_id: int) -> Dict:
        """Get a specific course from the CRM"""
        return self._make_request("GET", f"courses/{course_id}")
    
    def create_course(self, course_data: Dict) -> Dict:
        """Create a new course in the CRM"""
        return self._make_request("POST", "courses", data=course_data)
    
    def update_course(self, course_id: int, course_data: Dict) -> Dict:
        """Update a course in the CRM"""
        return self._make_request("PUT", f"courses/{course_id}", data=course_data)
    
    def delete_course(self, course_id: int) -> Dict:
        """Delete a course from the CRM"""
        return self._make_request("DELETE", f"courses/{course_id}")
    
    # Conversation-related methods
    def sync_conversation(self, conversation_data: Dict) -> Dict:
        """Sync a conversation with the CRM"""
        return self._make_request("POST", "conversations/sync", data=conversation_data)