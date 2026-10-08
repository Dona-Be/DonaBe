from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from src.api.frontend_paths import LOGIN_FAILED_PATH
from src.auth.google import GoogleLoginFailed
from src.core.config import settings
from src.domain.exceptions import UserAlreadyRegistered

HTTP_STATUS_BY_ERROR: dict[type[Exception], int] = {
    UserAlreadyRegistered: status.HTTP_409_CONFLICT,
}


def respond_with_error(request: Request, error: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_STATUS_BY_ERROR[type(error)], content={"detail": str(error)}
    )


def redirect_to_login_with_error(request: Request, error: Exception) -> RedirectResponse:
    return RedirectResponse(settings.frontend_page(LOGIN_FAILED_PATH))


def register_error_handlers(app: FastAPI) -> None:
    for error_type in HTTP_STATUS_BY_ERROR:
        app.add_exception_handler(error_type, respond_with_error)
    app.add_exception_handler(GoogleLoginFailed, redirect_to_login_with_error)
