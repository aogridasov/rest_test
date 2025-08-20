import logging
import sys

import uvicorn
from fastapi import FastAPI

from src.api.router import router

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
)


app = FastAPI(docs_url="/api/docs")


# Routers
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)
