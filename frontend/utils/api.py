# ==============================================================================
# API CLIENT - HTTP Requests to FastAPI Backend
# ==============================================================================
# This module handles all API communication with the FastAPI backend.
# ==============================================================================

import os
import requests
import streamlit as st
from functools import wraps
from typing import Optional, Dict, Any

# Load API URL from environment or use default
# Try to get from Streamlit secrets first (for Cloud deployment), then env vars
if hasattr(st, "secrets") and "API_URL" in st.secrets:
    API_URL = st.secrets["API_URL"]
else:
    API_URL = os.getenv("API_URL", "https://exam-scheduling-backend.onrender.com/api/v1")


class APIClient:
    """
    A simple API client for communicating with the FastAPI backend.
    Handles authentication tokens and common HTTP methods.
    """
    
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers including auth token if available."""
        headers = {"Content-Type": "application/json"}
        
        if "auth_token" in st.session_state and st.session_state.auth_token:
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
        
        return headers
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors."""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            error_detail = "Unknown error"
            try:
                error_detail = response.json().get("detail", str(http_err))
            except:
                error_detail = str(http_err)
            return {"error": True, "detail": error_detail, "status_code": response.status_code}
        except requests.exceptions.RequestException as req_err:
            return {"error": True, "detail": f"Connection error: {str(req_err)}"}
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a GET request to the API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, headers=self._get_headers(), params=params)
            return self._handle_response(response)
        except Exception as e:
            return {"error": True, "detail": str(e)}
    
    def post(self, endpoint: str, data: Optional[Dict] = None, is_form: bool = False) -> Dict[str, Any]:
        """Make a POST request to the API."""
        url = f"{self.base_url}{endpoint}"
        try:
            headers = self._get_headers()
            if is_form:
                # Remove Content-Type so requests can set it to application/x-www-form-urlencoded
                headers.pop("Content-Type", None)
                response = self.session.post(url, headers=headers, data=data)
            else:
                response = self.session.post(url, headers=headers, json=data)
            
            return self._handle_response(response)
        except Exception as e:
            return {"error": True, "detail": str(e)}
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a PUT request to the API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.put(url, headers=self._get_headers(), json=data)
            return self._handle_response(response)
        except Exception as e:
            return {"error": True, "detail": str(e)}
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request to the API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.delete(url, headers=self._get_headers())
            return self._handle_response(response)
        except Exception as e:
            return {"error": True, "detail": str(e)}


# Create a global API client instance
api = APIClient()


# ==============================================================================
# AUTHENTICATION HELPERS
# ==============================================================================

def login(email: str, password: str) -> Dict[str, Any]:
    """
    Login user and store token in session state.
    """
    # OAuth2PasswordRequestForm expects 'username' and 'password' as form data
    response = api.post(
        "/auth/login", 
        {"username": email, "password": password},
        is_form=True
    )
    
    if not response.get("error"):
        st.session_state.auth_token = response.get("access_token")
        # Since login doesn't return user info, we fetch it immediately
        user_response = api.get("/auth/me")
        if not user_response.get("error"):
            st.session_state.user = user_response
            st.session_state.is_authenticated = True
        else:
            return {"error": True, "detail": "Login successful but failed to fetch user info"}
    
    return response


def logout():
    """Clear authentication state."""
    if "auth_token" in st.session_state:
        del st.session_state.auth_token
    if "user" in st.session_state:
        del st.session_state.user
    st.session_state.is_authenticated = False


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return st.session_state.get("is_authenticated", False)


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current logged-in user."""
    return st.session_state.get("user")


def require_auth(func):
    """Decorator to require authentication for a page."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("⚠️ Please login to access this page")
            st.stop()
        return func(*args, **kwargs)
    return wrapper
