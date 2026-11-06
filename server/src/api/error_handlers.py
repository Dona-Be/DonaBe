import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from src.api.frontend_paths import LOGIN_FAILED_PATH
from src.auth.google import GoogleLoginError
from src.connectors.exceptions import ExternalServiceError
from src.core.config import settings
from src.domain.exceptions import (
    CepNotFoundError,
    CepWithoutCoordinatesError,
    CnpjNotFoundError,
    DomainError,
    InvalidCepError,
    InvalidCnpjError,
    RouteNotFoundError,
    UserAlreadyExistsError,
)

logger = logging.getLogger(__name__)

MAX_LOGGED_LENGTH = 200
RETRY_AFTER_SECONDS = "60"

HTTP_STATUS_BY_ERROR: dict[type[Exception], int] = {
    DomainError: status.HTTP_400_BAD_REQUEST,
    UserAlreadyExistsError: status.HTTP_409_CONFLICT,
    InvalidCnpjError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    InvalidCepError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    CepWithoutCoordinatesError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    CnpjNotFoundError: status.HTTP_404_NOT_FOUND,
    CepNotFoundError: status.HTTP_404_NOT_FOUND,
    RouteNotFoundError: status.HTTP_404_NOT_FOUND,
    ExternalServiceError: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def status_for(error: Exception) -> int:
    for error_type in type(error).__mro__:
        if error_type in HTTP_STATUS_BY_ERROR:
            return HTTP_STATUS_BY_ERROR[error_type]
    return status.HTTP_500_INTERNAL_SERVER_ERROR


def one_line(text: str) -> str:
    # repr keeps one line, so a forged newline cannot fake a log entry.
    return repr(text[:MAX_LOGGED_LENGTH])


def describe_cause(error: Exception) -> str:
    cause = error.__cause__
    if cause is None:
        cause = error
    return f"{type(cause).__name__} {one_line(str(cause))}"


def log_external_failure(error: ExternalServiceError) -> None:
    message = one_line(error.log_message)
    if error.__cause__ is None:
        logger.warning("%s", message)
    else:
        logger.warning("%s: %s", message, describe_cause(error))


def respond_with_error(request: Request, error: Exception) -> JSONResponse:
    if isinstance(error, ExternalServiceError):
        log_external_failure(error)
    status_code = status_for(error)
    headers = {}
    if status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
        headers["Retry-After"] = RETRY_AFTER_SECONDS
    return JSONResponse(status_code=status_code, content={"detail": str(error)}, headers=headers)


def redirect_to_login_with_error(request: Request, error: Exception) -> RedirectResponse:
    logger.warning("Google login failed: %s", describe_cause(error))
    return RedirectResponse(settings.frontend_page(LOGIN_FAILED_PATH))


def register_error_handlers(app: FastAPI) -> None:
    for error_type in HTTP_STATUS_BY_ERROR:
        app.add_exception_handler(error_type, respond_with_error)
    app.add_exception_handler(GoogleLoginError, redirect_to_login_with_error)
