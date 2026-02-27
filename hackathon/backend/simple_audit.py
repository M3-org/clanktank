"""
Simple audit logging focused on "who did what when" with minimal maintenance overhead.
"""

import functools
import sqlite3
from datetime import datetime


class SimpleAudit:
    def __init__(self, db_path: str = "data/hackathon.db"):
        self.db_path = db_path
        self._ensure_audit_table()

    def _ensure_audit_table(self):
        """Create simple audit table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simple_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_id TEXT,
                user_id TEXT,
                details TEXT
            )
        """)
        conn.commit()
        conn.close()

    def log(self, action: str, resource_id: str | None = None, user_id: str = "system", details: str | None = None):
        """Simple audit logging - just who did what when."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO simple_audit (timestamp, action, resource_id, user_id, details)
            VALUES (?, ?, ?, ?, ?)
        """,
            (datetime.now().isoformat(), action, resource_id, user_id, details),
        )
        conn.commit()
        conn.close()


# Global audit instance
_audit = None


def get_audit():
    """Get or create global audit instance."""
    global _audit
    if _audit is None:
        _audit = SimpleAudit()
    return _audit


# Simple decorator for automatic audit logging
def audit(action: str, get_resource_id=None, get_user_id=None):
    """
    Simple audit decorator - minimal boilerplate.

    @audit("submission_created", get_resource_id="submission_id", get_user_id="user_id")
    def create_submission(submission_id, user_id, ...):
        pass
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)

                # Extract IDs from function arguments
                resource_id = _extract_id(get_resource_id, args, kwargs) if get_resource_id else None
                user_id = _extract_id(get_user_id, args, kwargs) if get_user_id else "system"

                # Log the action
                get_audit().log(action, resource_id, user_id, f"function:{func.__name__}")

                return result
            except Exception as e:
                # Log failed attempts too
                resource_id = _extract_id(get_resource_id, args, kwargs) if get_resource_id else None
                user_id = _extract_id(get_user_id, args, kwargs) if get_user_id else "system"
                get_audit().log(f"{action}_failed", resource_id, user_id, f"error:{e!s}")
                raise

        return wrapper

    return decorator


def _extract_id(extractor, args, kwargs):
    """Extract ID from function arguments."""
    if isinstance(extractor, str):
        return kwargs.get(extractor)
    elif callable(extractor):
        return extractor(args, kwargs)
    return None


# Convenience functions for manual logging
def log_user_action(action: str, user_id: str, resource_id: str | None = None):
    """Log a user action."""
    get_audit().log(action, resource_id, user_id)


def log_system_action(action: str, resource_id: str | None = None):
    """Log a system action."""
    get_audit().log(action, resource_id, "system")


def log_security_event(event: str, details: str | None = None, user_id: str | None = None):
    """Log a security event with optional user context."""
    get_audit().log(f"security_{event}", None, user_id or "system", details)


# Quick aliases for common patterns
def audit_user_action(action: str):
    """Decorator for user actions - assumes 'user_id' parameter."""
    return audit(action, get_user_id="user_id")


def audit_submission_action(action: str):
    """Decorator for submission actions - assumes 'submission_id' and 'user_id' parameters."""
    return audit(action, get_resource_id="submission_id", get_user_id="user_id")


def audit_system_action(action: str):
    """Decorator for system actions."""
    return audit(action, get_user_id=lambda args, kwargs: "system")
