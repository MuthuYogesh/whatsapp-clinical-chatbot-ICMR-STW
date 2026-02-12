from fastapi import Request
from fastapi.responses import JSONResponse

async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches any unhandled error and prevents the server from 
    returning a raw stack trace to Meta.
    """
    print(f"🔥 SYSTEM CRASH: {str(exc)}")
    # Returning a 500. Tells Meta 'Something is wrong, please stop retrying for a moment'
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal Server Error"}
    )