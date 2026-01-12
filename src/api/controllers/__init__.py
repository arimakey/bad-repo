from .chat_controller import router as chat_router
from .health_controller import router as health_router
from .admin_controller import router as admin_router

__all__ = ["chat_router", "health_router", "admin_router"]
