from typing import Any

import httpx2
from authlib.common.errors import AuthlibBaseError
from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from joserfc.errors import JoseError
from starlette.requests import Request
from starlette.responses import Response

from src.core.config import settings
from src.domain.user_profile import UserProfile

GOOGLE_METADATA_URL = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_SCOPES = "openid email profile"
GOOGLE_ERRORS = (AuthlibBaseError, JoseError, httpx2.HTTPError, ValueError)


class GoogleLoginFailed(Exception):
    def __init__(self) -> None:
        super().__init__("Não foi possível entrar com o Google. Tente novamente.")


def register_google_app(client_id: str, client_secret: str) -> StarletteOAuth2App:
    return OAuth().register(
        name="google",
        server_metadata_url=GOOGLE_METADATA_URL,
        client_id=client_id,
        client_secret=client_secret,
        client_kwargs={"scope": GOOGLE_SCOPES},
    )


def extract_profile(userinfo: dict[str, Any]) -> UserProfile:
    email = userinfo.get("email")
    if not email or not userinfo.get("email_verified"):
        raise GoogleLoginFailed
    email = email.lower()
    return UserProfile(
        email=email, name=userinfo.get("name") or email, picture_url=userinfo.get("picture")
    )


class GoogleClient:
    def __init__(self, google_app: StarletteOAuth2App) -> None:
        self._google_app = google_app

    async def redirect_to_login(self, request: Request, callback_url: str) -> Response:
        try:
            return await self._google_app.authorize_redirect(request, callback_url)
        except GOOGLE_ERRORS as error:
            raise GoogleLoginFailed from error

    async def fetch_profile(self, request: Request) -> UserProfile:
        try:
            token = await self._google_app.authorize_access_token(request)
        except GOOGLE_ERRORS as error:
            raise GoogleLoginFailed from error
        return extract_profile(token.get("userinfo") or {})


google_client = GoogleClient(
    register_google_app(settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET)
)
