from collections.abc import Callable
from typing import Any

import httpx2
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.frontend_paths import LOGIN_FAILED_PATH, LOGIN_PATH
from src.core.config import settings
from src.domain.user_profile import UserProfile
from src.models.notification import Notification
from src.models.user import Donor
from tests.connectors.samples import AACD_TAX_ID
from tests.fakes import USER_EMAIL, USER_NAME, USER_PICTURE

SITE_URL = settings.frontend_page()
LOGIN_URL = settings.frontend_page(LOGIN_PATH)
LOGIN_FAILED_URL = settings.frontend_page(LOGIN_FAILED_PATH)
GOOGLE_CALLBACK = "/api/auth/callback/google"
ACCESS_TOKEN_COOKIE = "access_token"
PENDING_SIGNUP_COOKIE = "pending_signup"
DONOR_SIGNUP = {"postal_code": "01310-200", "preferred_causes": ["animals", "health"]}
PENDING_PROFILE = {
    "email": USER_EMAIL,
    "name": USER_NAME,
    "picture_url": USER_PICTURE,
    "phone": None,
    "role": None,
    "postal_code": None,
    "preferred_causes": None,
}
MANAGER_PROFILE = {**PENDING_PROFILE, "role": "manager"}
DONOR_PROFILE = {
    **PENDING_PROFILE,
    "role": "donor",
    "postal_code": "01310200",
    "preferred_causes": ["animals", "health"],
}
NOTIFICATION_MESSAGE = "Sua doação para a necessidade Ração mudou para Em contato."
Notify = Callable[..., Notification]
INSTITUTIONS = "/api/institutions"
MY_INSTITUTIONS = f"{INSTITUTIONS}/me"
# What the API answers for the AACD sample of the CNPJ connector.
INSTITUTION_PREVIEW = {
    "type": "association",
    "cnpj": AACD_TAX_ID,
    "legal_name": "ASSOCIACAO DE ASSISTENCIA A CRIANCA DEFICIENTE",
    "trade_name": "Aacd Ibirapuera",
    "street": "Avenida Prof Ascendino Reis",
    "number": "724",
    "complement": None,
    "neighborhood": "VL Clementino",
    "city": "São Paulo",
    "state": "SP",
    "postal_code": "04027000",
    "verdict": "nonprofit",
    "reasons": [
        "OK - Situação cadastral: Ativa",
        "OK - Natureza jurídica: 3999 - Associação Privada",
        "NÃO - Atividade principal: 8630501 - Atividade médica ambulatorial",
    ],
}
INSTITUTION = {
    **INSTITUTION_PREVIEW,
    "id": 1,
    "description": None,
    "causes": [],
    "phone": None,
    "contact_email": None,
    "website": None,
    "instagram": None,
    "facebook": None,
}
OPTIONAL_DETAILS = {
    "trade_name": "AACD",
    "description": "Reabilitação de crianças com deficiência.",
    "phone": "1120000000",
    "contact_email": "contato@exemplo.org",
    "website": "https://exemplo.org",
    "instagram": "https://instagram.com/exemplo",
    "facebook": "https://facebook.com/exemplo",
    "complement": "Sala 2",
}
INSTITUTION_DETAILS = {
    **OPTIONAL_DETAILS,
    "causes": ["health", "people_with_disabilities"],
    "street": "Avenida Paulista",
    "number": "1000",
    "neighborhood": "Bela Vista",
    "city": "Campinas",
    "state": "RJ",
    "postal_code": "01310200",
}


def create_donor(db_session: Session, email: str = USER_EMAIL) -> Donor:
    donor = Donor.from_profile(UserProfile(email=email, name=USER_NAME, picture_url=None))
    db_session.add(donor)
    db_session.commit()
    return donor


def cookies_set_by(response: httpx2.Response) -> dict[str, str]:
    return {header.split("=", 1)[0]: header for header in response.headers.get_list("set-cookie")}


def was_deleted(cookie_header: str) -> bool:
    return "Max-Age=0" in cookie_header


def sign_up(client: TestClient, role: str, data: dict[str, Any] | None = None) -> httpx2.Response:
    client.get(GOOGLE_CALLBACK, follow_redirects=False)
    return client.post(f"/api/profiles/{role}", json=data)


def look_up(client: TestClient, cnpj: str = AACD_TAX_ID) -> httpx2.Response:
    return client.get(f"{INSTITUTIONS}/lookup", params={"cnpj": cnpj})


def register(client: TestClient, cnpj: str = AACD_TAX_ID, **details: Any) -> httpx2.Response:
    return client.post(INSTITUTIONS, json={"cnpj": cnpj, **details})
