from contextvars import ContextVar
from typing import Optional, Dict, Any

# Context variable to store current request's user information
_request_user_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "request_user_context", default=None
)


def set_request_user(user_info: Dict[str, Any]) -> None:
    """Set the current request's user information"""
    _request_user_context.set(user_info)


def get_request_user() -> Optional[Dict[str, Any]]:
    """Get the current request's user information"""
    return _request_user_context.get()


def get_user_timezone() -> str:
    """Get the current user's timezone or default to UTC"""
    user_info = get_request_user()
    if user_info and "timezone" in user_info:
        return user_info["timezone"]
    return "UTC"


def clear_request_context() -> None:
    """Clear the request context"""
    _request_user_context.set(None)
