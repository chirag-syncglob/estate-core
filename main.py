from fastapi import FastAPI

from app.core.exception_handlers import add_exception_handlers, add_request_context_middleware
from app.modules import api_router


def start_application():
    app = FastAPI(
        title="Estate Core Application",
        description="A simple SaaS product backend",
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
    )

    add_request_context_middleware(app)
    add_exception_handlers(app)

    app.include_router(
        prefix="/api/v1",
        router=api_router,
    )

    return app


app = start_application()
