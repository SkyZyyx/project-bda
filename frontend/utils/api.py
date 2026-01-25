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
import time

# Import storage utilities for session persistence
from utils.storage import (
    save_auth_session,
    clear_all_auth_storage,
    restore_session_from_storage,
    decode_token_exp,
    is_token_expired,
)

# Load API URL from environment or use default
# Try to get from Streamlit secrets first (for Cloud deployment), then env vars
if hasattr(st, "secrets") and "API_URL" in st.secrets:
    API_URL = st.secrets["API_URL"]
else:
    API_URL = os.getenv(
        "API_URL", "https://exam-scheduling-backend.onrender.com/api/v1"
    )

# Base URL for health checks (without /api/v1)
BASE_URL = API_URL.replace("/api/v1", "")


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
            return {
                "error": True,
                "detail": error_detail,
                "status_code": response.status_code,
            }
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

    def post(
        self, endpoint: str, data: Optional[Dict] = None, is_form: bool = False
    ) -> Dict[str, Any]:
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
    Login user and store token in session state AND localStorage.
    """
    # OAuth2PasswordRequestForm expects 'username' and 'password' as form data
    response = api.post(
        "/auth/login", {"username": email, "password": password}, is_form=True
    )

    if not response.get("error"):
        token = response.get("access_token")
        if token:
            st.session_state.auth_token = token

            # Since login doesn't return user info, we fetch it immediately
            user_response = api.get("/auth/me")
            if not user_response.get("error"):
                st.session_state.user = user_response
                st.session_state.is_authenticated = True

                # PERSIST TO LOCALSTORAGE for session persistence across refreshes
                # Extract token expiration
                token_exp = decode_token_exp(token)
                save_auth_session(token, user_response, token_exp)
            else:
                return {
                    "error": True,
                    "detail": "Login successful but failed to fetch user info",
                }

    return response


def logout():
    """Clear authentication state from session AND localStorage."""
    if "auth_token" in st.session_state:
        del st.session_state.auth_token
    if "user" in st.session_state:
        del st.session_state.user
    st.session_state.is_authenticated = False

    # Clear from localStorage
    clear_all_auth_storage()


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


def restore_session() -> bool:
    """
    Restore authentication session from localStorage if available.

    This function should be called on app startup to check if the user
    has a valid session stored in their browser.

    Returns:
        True if session was restored, False otherwise
    """
    # Check if already authenticated in current Streamlit session
    if is_authenticated():
        return True

    # Try to restore from localStorage
    session_data = restore_session_from_storage()

    if session_data:
        token = session_data.get("token")
        user_data = session_data.get("user")
        token_exp = session_data.get("exp")

        # Check if token is expired
        if token and user_data:
            if token_exp and is_token_expired(token_exp):
                # Token expired - clear storage
                clear_all_auth_storage()
                return False

            # Token is valid - restore session state
            st.session_state.auth_token = token
            st.session_state.user = user_data
            st.session_state.is_authenticated = True

            return True

    return False


# ==============================================================================
# BACKEND WAKE-UP FUNCTIONS
# ==============================================================================


def check_backend_health(timeout: int = 60, retry_interval: int = 3) -> bool:
    """
    Check if backend is awake and responding.

    Args:
        timeout: Maximum time to wait in seconds (default: 60)
        retry_interval: Seconds between retry attempts (default: 3)

    Returns:
        True if backend is healthy, False on timeout
    """
    start_time = time.time()
    attempts = 0
    max_attempts = timeout // retry_interval

    while time.time() - start_time < timeout:
        attempts += 1
        try:
            # Ping the health endpoint
            response = requests.get(
                f"{BASE_URL}/health",
                timeout=5,  # 5 second timeout per request
            )

            if response.status_code == 200:
                return True

        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            # Backend not ready yet, continue waiting
            pass

        # Don't sleep on the last attempt
        if attempts < max_attempts:
            time.sleep(retry_interval)

    return False


def wake_backend() -> bool:
    """
    Wake up the backend with a professional loading screen.

    Returns:
        True if backend woke up successfully, False on timeout
    """
    # Create a placeholder for the loading screen
    loading_container = st.empty()

    with loading_container.container():
        # Show professional header
        st.markdown(
            """
        <div style="text-align: center; padding: 2rem 0;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        width: 80px; height: 80px; border-radius: 20px; 
                        display: inline-flex; align-items: center; justify-content: center; 
                        color: white; font-weight: 800; font-size: 2.5rem; margin-bottom: 1rem;">
                E
            </div>
            <h1 style="font-size: 2rem; font-weight: 800; margin: 0.5rem 0;">ExamOpti</h1>
            <p style="color: #888; font-size: 1rem;">Strategic Scheduling Platform</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Show loading message
        st.info("""
        ⏳ **Initializing Backend System**
        
        The backend is hosted on a free tier service and goes to sleep when inactive.
        This is a one-time delay while the service wakes up.
        
        **⏱️ Usually takes 30-60 seconds...**
        
        Subsequent requests will be instant once the backend is warm.
        """)

        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Start timing
        start_time = time.time()
        timeout = 60
        retry_interval = 3

        # Try to wake up backend
        attempts = 0
        max_attempts = timeout // retry_interval

        while time.time() - start_time < timeout:
            attempts += 1
            elapsed = int(time.time() - start_time)

            # Update progress
            progress = min(elapsed / timeout, 0.95)  # Cap at 95% until success
            progress_bar.progress(progress)
            status_text.text(f"Attempt {attempts}/{max_attempts} • Elapsed: {elapsed}s")

            try:
                # Ping the health endpoint
                response = requests.get(f"{BASE_URL}/health", timeout=5)

                if response.status_code == 200:
                    # Success!
                    progress_bar.progress(1.0)
                    status_text.text(f"✅ Backend ready! (took {elapsed}s)")
                    time.sleep(0.5)  # Brief pause to show success
                    loading_container.empty()  # Clear the loading screen
                    return True

            except (requests.exceptions.RequestException, requests.exceptions.Timeout):
                # Backend not ready yet, continue waiting
                pass

            # Don't sleep on the last attempt
            if attempts < max_attempts:
                time.sleep(retry_interval)

        # Timeout reached
        progress_bar.empty()
        status_text.empty()
        st.error("""
        ❌ **Backend Wake-Up Timeout**
        
        The backend service is taking longer than expected to wake up.
        This can happen if the service is experiencing high load.
        
        **Please try:**
        1. Refreshing the page
        2. Waiting a minute and trying again
        3. Checking the backend URL directly: https://exam-scheduling-backend.onrender.com/health
        """)

        if st.button("🔄 Retry Now"):
            st.rerun()

        st.stop()
        return False
