"""
Rate Limiting Configuration
Implements IP-based rate limiting using slowapi
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_real_client_ip(request: Request) -> str:
    """
    Get client IP address, accounting for proxy headers

    Args:
        request: FastAPI request

    Returns:
        Client IP address
    """
    # Check for X-Forwarded-For header (proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded.split(",")[0].strip()

    # Check for X-Real-IP header (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct connection IP
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=["200/hour"],  # Default: 200 requests per hour per IP
    storage_uri="memory://",  # In-memory storage (can be replaced with Redis for production)
)


# Rate limit configurations for different endpoints
RATE_LIMITS = {
    # Health check - very permissive
    "health": "60/minute",
    # Task creation - stricter limit
    "create_task": "10/hour",
    # File upload - very strict (resource intensive)
    "upload_file": "20/hour",
    # KB operations - moderate limit
    "kb_mutations": "30/hour",
    # Read operations - permissive
    "read_operations": "300/hour",
    # Report generation - strict (resource intensive)
    "generate_report": "10/hour",
}
