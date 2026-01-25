# ==============================================================================
# BROWSER STORAGE UTILITIES - localStorage Persistence
# ==============================================================================
# This module provides functions to interact with browser localStorage via JavaScript.
# Used to persist authentication tokens across page refreshes and browser sessions.
# ==============================================================================

import streamlit as st
import streamlit.components.v1 as components
import json
from typing import Optional, Any, Dict
from datetime import datetime, timezone


# Storage keys for localStorage
AUTH_TOKEN_KEY = "exam_opti_auth_token"
USER_DATA_KEY = "exam_opti_user"
TOKEN_EXP_KEY = "exam_opti_token_exp"


def save_to_local_storage(key: str, value: Any) -> None:
    """
    Save a value to browser localStorage using JavaScript.

    Args:
        key: The storage key
        value: The value to store (will be JSON serialized)
    """
    # Convert value to JSON string
    json_value = json.dumps(value)

    # JavaScript code to save to localStorage
    js_code = f"""
    <script>
        localStorage.setItem('{key}', '{json_value}');
    </script>
    """

    # Execute JavaScript in Streamlit
    components.html(js_code, height=0, width=0)


def get_from_local_storage(key: str) -> Optional[Any]:
    """
    Get a value from browser localStorage.

    Note: This is a workaround since Streamlit can't directly read localStorage.
    We use a hidden input field that JavaScript populates on page load.

    Args:
        key: The storage key

    Returns:
        The stored value, or None if not found
    """
    # This is a limitation of Streamlit - we can't directly read localStorage
    # Instead, we'll use query parameters as a fallback
    # The proper implementation requires the restore_session_from_storage() function
    return None


def clear_local_storage(key: str) -> None:
    """
    Remove a value from browser localStorage.

    Args:
        key: The storage key to remove
    """
    js_code = f"""
    <script>
        localStorage.removeItem('{key}');
    </script>
    """

    components.html(js_code, height=0, width=0)


def clear_all_auth_storage() -> None:
    """
    Clear all authentication-related data from localStorage.
    Called on logout.
    """
    js_code = f"""
    <script>
        localStorage.removeItem('{AUTH_TOKEN_KEY}');
        localStorage.removeItem('{USER_DATA_KEY}');
        localStorage.removeItem('{TOKEN_EXP_KEY}');
    </script>
    """

    components.html(js_code, height=0, width=0)


def save_auth_session(
    token: str, user_data: Dict[str, Any], token_exp: Optional[int] = None
) -> None:
    """
    Save complete authentication session to localStorage.

    Args:
        token: JWT access token
        user_data: User information dictionary
        token_exp: Token expiration timestamp (optional)
    """
    # Save token
    save_to_local_storage(AUTH_TOKEN_KEY, token)

    # Save user data
    save_to_local_storage(USER_DATA_KEY, user_data)

    # Save expiration if provided
    if token_exp:
        save_to_local_storage(TOKEN_EXP_KEY, token_exp)


def restore_session_from_storage() -> Optional[Dict[str, Any]]:
    """
    Restore authentication session from localStorage.

    This function uses a JavaScript bridge to read localStorage and pass
    the data back to Streamlit via query parameters.

    Returns:
        Dictionary with 'token', 'user', 'exp' if session exists, None otherwise
    """
    # Use a unique session ID to prevent conflicts
    session_restore_key = "session_restore_complete"

    # Check if we've already restored this session
    if session_restore_key in st.session_state:
        return None

    # JavaScript to read localStorage and reload page with query params
    js_code = f"""
    <script>
        // Check if we've already tried to restore
        const urlParams = new URLSearchParams(window.location.search);
        const hasToken = urlParams.has('auth_token');
        
        if (!hasToken) {{
            // First load - check localStorage
            const token = localStorage.getItem('{AUTH_TOKEN_KEY}');
            const userData = localStorage.getItem('{USER_DATA_KEY}');
            const tokenExp = localStorage.getItem('{TOKEN_EXP_KEY}');
            
            if (token && userData) {{
                // Token exists - reload with query params
                const url = new URL(window.location);
                url.searchParams.set('auth_token', token);
                url.searchParams.set('user_data', userData);
                if (tokenExp) {{
                    url.searchParams.set('token_exp', tokenExp);
                }}
                url.searchParams.set('restore', '1');
                window.location.href = url.toString();
            }}
        }}
    </script>
    """

    # Check if we're on a restore reload
    query_params = st.query_params

    if query_params.get("restore") == "1":
        # We're on the restore reload - extract data
        token = query_params.get("auth_token")
        user_data_str = query_params.get("user_data")
        token_exp_str = query_params.get("token_exp")

        if token and user_data_str:
            try:
                # Parse user data
                user_data = json.loads(user_data_str)

                # Parse expiration if available
                token_exp = None
                if token_exp_str:
                    try:
                        token_exp = int(token_exp_str)
                    except:
                        pass

                # Mark session as restored
                st.session_state[session_restore_key] = True

                # Clear query params to clean URL
                st.query_params.clear()

                return {"token": token, "user": user_data, "exp": token_exp}
            except json.JSONDecodeError:
                # Invalid data - clear it
                clear_all_auth_storage()
                st.query_params.clear()
                return None
    else:
        # First load - inject JavaScript to check localStorage
        components.html(js_code, height=0, width=0)
        return None


def is_token_expired(token_exp: Optional[int]) -> bool:
    """
    Check if a token is expired based on its expiration timestamp.

    Args:
        token_exp: Unix timestamp of token expiration

    Returns:
        True if expired, False if still valid
    """
    if not token_exp:
        return True

    current_time = datetime.now(timezone.utc).timestamp()
    return current_time >= token_exp


def decode_token_exp(token: str) -> Optional[int]:
    """
    Decode JWT token to extract expiration timestamp WITHOUT validating signature.
    This is safe because we only use it to check expiration, not for authentication.

    Args:
        token: JWT token string

    Returns:
        Unix timestamp of expiration, or None if invalid
    """
    try:
        # Try to import jwt
        import jwt

        # Decode without verification (we only need the exp claim)
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get("exp")
    except ImportError:
        # jwt library not available - use simpler base64 decode
        try:
            import base64

            # JWT format: header.payload.signature
            parts = token.split(".")
            if len(parts) != 3:
                return None

            # Decode payload (second part)
            # Add padding if needed
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding

            payload_json = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_json)

            return payload.get("exp")
        except:
            return None
    except:
        return None
