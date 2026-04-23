from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.middleware import RequestIDMiddleware

setup_logging(log_level=settings.log_level, log_format=settings.log_format)

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(RequestIDMiddleware)


@app.get("/")
def root():
    return {"message": "TM Airlines RAG Service"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
