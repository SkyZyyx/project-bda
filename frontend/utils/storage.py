# ==============================================================================
# BROWSER STORAGE UTILITIES - Query Parameter-Based Session Persistence
# ==============================================================================
# This uses Streamlit's query_params + localStorage for reliable session persistence
# ==============================================================================

import streamlit as st
import streamlit.components.v1 as components
import json
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timezone


# Storage keys
AUTH_TOKEN_KEY = "exam_opti_auth_token"
USER_DATA_KEY = "exam_opti_user"


def save_auth_session(token: str, user_data: Dict[str, Any]) -> None:
    """
    Save authentication session to BOTH Streamlit query params AND localStorage.
    Query params survive page refresh, localStorage survives tab close.
    """
    try:
        # Encode data for URL safety
        token_b64 = base64.urlsafe_b64encode(token.encode()).decode()
        user_json = json.dumps(user_data)
        user_b64 = base64.urlsafe_b64encode(user_json.encode()).decode()

        # Save to Streamlit query params (persists across refresh)
        st.query_params["auth_token"] = token_b64
        st.query_params["user_data"] = user_b64

        # ALSO save to localStorage for cross-tab support
        user_data_escaped = user_json.replace("\\", "\\\\").replace('"', '\\"')
        token_escaped = token.replace("\\", "\\\\").replace('"', '\\"')

        js_code = f"""
        <script>
            try {{
                localStorage.setItem('{AUTH_TOKEN_KEY}', "{token_escaped}");
                localStorage.setItem('{USER_DATA_KEY}', "{user_data_escaped}");
            }} catch (e) {{
                console.error('localStorage save failed:', e);
            }}
        </script>
        """
        components.html(js_code, height=0)

    except Exception as e:
        st.error(f"Failed to save session: {e}")


def clear_all_auth_storage() -> None:
    """
    Clear authentication from BOTH query params AND localStorage.
    """
    # Clear query params
    if "auth_token" in st.query_params:
        del st.query_params["auth_token"]
    if "user_data" in st.query_params:
        del st.query_params["user_data"]

    # Clear localStorage
    js_code = f"""
    <script>
        try {{
            localStorage.removeItem('{AUTH_TOKEN_KEY}');
            localStorage.removeItem('{USER_DATA_KEY}');
        }} catch (e) {{
            console.error('localStorage clear failed:', e);
        }}
    </script>
    """
    components.html(js_code, height=0)


def restore_session_from_query_params() -> Optional[Dict[str, Any]]:
    """
    Restore session from Streamlit query parameters.
    This is the PRIMARY method that actually works reliably.
    """
    try:
        # Check if auth data is in query params
        if "auth_token" in st.query_params and "user_data" in st.query_params:
            # Decode from base64
            token_b64 = st.query_params["auth_token"]
            user_b64 = st.query_params["user_data"]

            token = base64.urlsafe_b64decode(token_b64.encode()).decode()
            user_json = base64.urlsafe_b64decode(user_b64.encode()).decode()
            user_data = json.loads(user_json)

            # Check token expiration
            token_exp = decode_token_exp(token)
            if token_exp and is_token_expired(token_exp):
                # Token expired - clear everything
                clear_all_auth_storage()
                return None

            return {"token": token, "user": user_data, "exp": token_exp}
    except Exception as e:
        # Invalid data in query params - clear it
        if "auth_token" in st.query_params:
            del st.query_params["auth_token"]
        if "user_data" in st.query_params:
            del st.query_params["user_data"]

    return None


def decode_token_exp(token: str) -> Optional[int]:
    """
    Decode JWT token to extract expiration timestamp.
    """
    try:
        # JWT format: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            return None

        # Decode payload (second part)
        payload_b64 = parts[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        payload_json = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_json)

        return payload.get("exp")
    except Exception:
        return None


def is_token_expired(token_exp: Optional[int]) -> bool:
    """
    Check if token is expired.
    """
    if not token_exp:
        return True

    current_time = datetime.now(timezone.utc).timestamp()
    return current_time >= token_exp
