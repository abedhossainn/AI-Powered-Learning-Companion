from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionCORSMiddleware(BaseHTTPMiddleware):
    """
    Production middleware to force CORS headers on all responses
    """
    
    def __init__(self, app, allowed_origins=None):
        super().__init__(app)
        # Use specific origins for security
        self.allowed_origins = allowed_origins or ["https://ailearning.cbtbags.com"]
        logger.info(f"Initialized Production CORS Middleware with allowed origins: {self.allowed_origins}")
        
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")
        logger.info(f"Request from origin: {origin}")
        
        # For preflight requests (OPTIONS), return immediately with CORS headers
        if request.method == "OPTIONS":
            headers = {
                "Access-Control-Allow-Origin": origin if origin in self.allowed_origins else "",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "86400"  # Cache preflight for 24 hours
            }
            return Response(content="", status_code=200, headers=headers)
            
        # For regular requests, add CORS headers to the response
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Error in request processing: {str(e)}")
            
            # Even for errors, we need to add CORS headers
            error_response = Response(
                content=str(e),
                status_code=500
            )
            if origin in self.allowed_origins:
                error_response.headers["Access-Control-Allow-Origin"] = origin
                error_response.headers["Access-Control-Allow-Credentials"] = "true"
            return error_response
        
        # Add CORS headers to all responses
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept"
        
        logger.info(f"Response status: {response.status_code}, added CORS headers")
        return response
