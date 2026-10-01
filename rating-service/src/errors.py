from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.schemas import ErrorDescription, ValidationErrorResponse

VALIDATION_ERROR_MESSAGE = "Validation failed"
BODY_LOCATION_PREFIX = "body"


def _field_name(location: tuple[str | int, ...]) -> str:
    parts = [str(part) for part in location if str(part) != BODY_LOCATION_PREFIX]
    return ".".join(parts) if parts else BODY_LOCATION_PREFIX


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Подменяет стандартный 422 FastAPI на 400 из контракта."""
    errors = [
        ErrorDescription(field=_field_name(error["loc"]), error=error["msg"])
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ValidationErrorResponse(
            message=VALIDATION_ERROR_MESSAGE, errors=errors
        ).model_dump(by_alias=True),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_error_handler)
