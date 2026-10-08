from typing import Any

from fastapi.responses import RedirectResponse
from starlette.requests import Request

USER_EMAIL = "maria@exemplo.com"
USER_NAME = "Maria"
USER_PICTURE = "https://exemplo.com/maria.png"


def google_token(email: str = USER_EMAIL) -> dict[str, Any]:
    userinfo = {"email": email, "email_verified": True, "name": USER_NAME, "picture": USER_PICTURE}
    return {"access_token": "google-token", "userinfo": userinfo}


class FakeGoogleApp:
    def __init__(self, token: dict[str, Any]) -> None:
        self.token = token
        self.error: Exception | None = None

    async def authorize_redirect(self, request: Request, callback_url: str) -> RedirectResponse:
        if self.error is not None:
            raise self.error
        # Authlib answers 302, like the real Google client.
        return RedirectResponse(f"https://accounts.google.com/?redirect_uri={callback_url}", 302)

    async def authorize_access_token(self, request: Request) -> dict[str, Any]:
        if self.error is not None:
            raise self.error
        return self.token
