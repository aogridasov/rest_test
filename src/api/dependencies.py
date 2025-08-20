from typing import Annotated

from fastapi import Depends, HTTPException, status, security
from sqlalchemy.ext.asyncio import AsyncSession

from src.settings import settings
from src.db.base import get_db_session

DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


api_key_query = security.APIKeyQuery(name="api_key", auto_error=True)


async def get_static_api_key(api_key: str = Depends(api_key_query)):
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный ключ доступа",
        )

ApiKeyDep = Depends(get_static_api_key)
