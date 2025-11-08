import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from huggingface_hub import HfApi
from huggingface_hub.utils import HfHubHTTPError

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


async def get_current_user(token: str | None = Depends(oauth2_scheme)) -> dict:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        hf_api = HfApi(token=token)
        user_info = hf_api.whoami()
        if (
            user_info.get("auth", {}).get("accessToken", {}).get("role")
            == "fineGrained"
        ):
            permissions = user_info["auth"]["accessToken"].get("permissions", [])
            if "read" not in permissions:
                pass
        logger.info(f"Authenticated user: {user_info.get('name')}")
        return user_info
    except HfHubHTTPError as e:
        logger.exception(f"Hugging Face authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Hugging Face token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.exception(f"An unexpected error occurred during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication",
        )