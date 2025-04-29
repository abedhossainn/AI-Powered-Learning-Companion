"""
Simple CORS Proxy for development purposes.
This proxy will forward requests to the backend API while handling CORS headers.
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn
from starlette.background import BackgroundTask
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS with permissive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Very permissive for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BACKEND_URL = "http://localhost:8001"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def proxy(request: Request, path: str):
    logger.info(f"Received request: {request.method} /{path}")
    
    # Construct the target URL
    url = f"{BACKEND_URL}/{path}"
    
    # Prepare headers, removing host to avoid conflicts
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # Get query parameters
    params = dict(request.query_params)
    
    # Get request body
    body = await request.body()
    
    # Log request details
    logger.info(f"Proxying to: {url}")
    logger.info(f"Headers: {headers}")
    
    async with httpx.AsyncClient() as client:
        try:
            # Forward the request to the actual backend
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=params,
                content=body,
                follow_redirects=True
            )
            
            # Log response details
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            
            # Create a response that mirrors the backend response but with added CORS headers
            content = response.content
            headers = dict(response.headers)
            
            # Add CORS headers regardless of what the backend returns
            headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
            headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, Origin, X-Requested-With"
            
            # Create the response
            return Response(
                content=content,
                status_code=response.status_code,
                headers=headers,
                media_type=response.headers.get("content-type")
            )
        except Exception as e:
            logger.error(f"Error proxying request: {str(e)}")
            
            # Return error with CORS headers
            return Response(
                content=str(e),
                status_code=500,
                headers={
                    "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
                    "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, Origin, X-Requested-With"
                }
            )

if __name__ == "__main__":
    logger.info("Starting CORS proxy on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002)