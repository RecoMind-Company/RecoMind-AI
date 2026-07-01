"""
API Module
==========
Re-exports router and dependencies
"""

from api.routes import router as api_router, mock_router
from api.dependencies import verify_api_key

__all__ = ["api_router", "mock_router", "verify_api_key"]
