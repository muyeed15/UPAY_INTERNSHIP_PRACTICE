import logging
import time

# Author Information
__author__ = "Syed Abdullah Al Muyeed"
__email__ = "muyeed.al.abdullah@gmail.com"

# Logger by name
logger = logging.getLogger("request_logger")


# Calls __init__ once at startup, then __call__ on every request
class RequestLoggingMiddleware:

    # Passes get_response
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Record the time before the view runs
        start_time = time.time()

        # Runs the view and returns a response
        response = self.get_response(request)

        # Calculate how long the view took
        duration_ms = (time.time() - start_time) * 1000

        # HTTP_X_FORWARDED_FOR is set by load balancers/proxies and contains the real client IP
        # REMOTE_ADDR is the direct connection IP, falls back to this if no proxy
        ip = request.META.get(
            "HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "unknown")
        )

        # HTTP_USER_AGENT is the browser/client description sent by the requester
        user_agent = request.META.get("HTTP_USER_AGENT", "unknown")

        # Write one log line per request
        logger.info(
            f"path={request.path} method={request.method} "
            f"status={response.status_code} ip={ip} "
            f'duration={duration_ms:.2f}ms user_agent="{user_agent}"'
        )

        # Always return the response
        return response
