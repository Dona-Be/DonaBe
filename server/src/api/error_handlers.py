import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from src.api.frontend_paths import LOGIN_FAILED_PATH
from src.auth.google import GoogleLoginError
from src.core.config import settings
from src.domain.exceptions import UserAlreadyExistsError

logger = logging.getLogger(__name__)

MAX_LOGGED_CAUSE_LENGTH = 200

HTTP_STATUS_BY_ERROR: dict[type[Exception], int] = {
    UserAlreadyExistsError: status.HTTP_409_CONFLICT,
}


def status_for(error: Exception) -> int:
    return next(
        HTTP_STATUS_BY_ERROR[error_type]
        for error_type in type(error).__mro__
        if error_type in HTTP_STATUS_BY_ERROR
    )


def respond_with_error(request: Request, error: Exception) -> JSONResponse:
    return JSONResponse(status_code=status_for(error), content={"detail": str(error)})


def redirect_to_login_with_error(request: Request, error: Exception) -> RedirectResponse:
    cause = error.__cause__ or error
    logger.warning(
        "Google login failed: %s %r", type(cause).__name__, str(cause)[:MAX_LOGGED_CAUSE_LENGTH]
    )
    return RedirectResponse(settings.frontend_page(LOGIN_FAILED_PATH))


def register_error_handlers(app: FastAPI) -> None:
    for error_type in HTTP_STATUS_BY_ERROR:
        app.add_exception_handler(error_type, respond_with_error)
    app.add_exception_handler(GoogleLoginError, redirect_to_login_with_error)
