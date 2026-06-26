import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
import uuid

logger = logging.getLogger("tides_api")

class APIException(Exception):
    """Base API Exception."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class StartupNotFoundError(APIException):
    def __init__(self, startup_id: str):
        super().__init__(f"Startup with ID {startup_id} not found", status.HTTP_404_NOT_FOUND)

class DocumentNotFoundError(APIException):
    def __init__(self, document_id: str):
        super().__init__(f"Document with ID {document_id} not found", status.HTTP_404_NOT_FOUND)

class EvaluationNotFoundError(APIException):
    def __init__(self, startup_id: str):
        super().__init__(f"Evaluation graph not found for startup {startup_id}", status.HTTP_404_NOT_FOUND)

def make_error_response(request: Request, message: str, status_code: int) -> JSONResponse:
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": None,
            "metadata": {},
            "request_id": req_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "detail": message
        }
    )

def setup_exception_handlers(app):
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        logger.error(f"API Error: {exc.message}")
        return make_error_response(request, exc.message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation Error: {exc.errors()}")
        err_msg = "; ".join([f"{'.'.join(str(l) for l in err['loc'])}: {err['msg']}" for err in exc.errors()])
        return make_error_response(request, f"Validation Failed: {err_msg}", status.HTTP_422_UNPROCESSABLE_ENTITY)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(f"HTTP Error: {exc.detail}")
        return make_error_response(request, exc.detail, exc.status_code)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Internal Server Error")
        return make_error_response(request, f"Internal Server Error: {str(exc)}", status.HTTP_500_INTERNAL_SERVER_ERROR)
