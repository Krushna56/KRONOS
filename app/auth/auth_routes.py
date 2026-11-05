"""Deprecated compatibility import for the canonical API auth router.

The old in-memory admin/admin login has been removed. Authentication is now
handled by app.api.routes.auth and its database-backed user records.
"""

from app.api.routes.auth import router
