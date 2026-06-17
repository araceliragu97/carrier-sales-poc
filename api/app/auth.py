from fastapi import Header, HTTPException, status

from app.config import settings


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """
    Every endpoint depends on this. FastAPI will reject the request with a 422
    automatically if the header is missing entirely (since it's a required Header),
    and we raise 401 ourselves if the key is present but wrong.
    """
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
