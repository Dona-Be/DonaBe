import httpx2
import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from src.api.dependencies import CnpjServiceDep, LocationServiceDep, get_http_client
from src.api.error_handlers import register_error_handlers
from tests.connectors.fakes import FakeApi, no_network_client
from tests.connectors.samples import AACD, CEP_NOT_FOUND, PAULISTA

TAX_ID = "60979457000111"


def app_with_routes() -> FastAPI:
    # A throwaway app, so the wiring is checked without the database routes.
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/cnpj/{cnpj}")
    def classify(cnpj: str, service: CnpjServiceDep) -> dict[str, str]:
        return {"verdict": service.classify(cnpj).classification.verdict}

    @app.get("/cep/{cep}")
    def locate(cep: str, service: LocationServiceDep) -> dict[str, str]:
        return {"city": service.locate(cep).city}

    return app


def client_with(api_client: httpx2.Client) -> TestClient:
    app = app_with_routes()
    app.dependency_overrides[get_http_client] = lambda: api_client
    return TestClient(app)


def test_every_request_shares_one_http_client() -> None:
    assert isinstance(get_http_client(), httpx2.Client)
    assert get_http_client() is get_http_client()


def test_the_cnpj_service_reaches_cnpja_through_the_http_client_of_the_app() -> None:
    api = FakeApi(httpx2.Response(200, json=AACD))

    response = client_with(api.client()).get(f"/cnpj/{TAX_ID}")

    assert response.json() == {"verdict": "nonprofit"}
    assert str(api.requests[0].url) == f"https://open.cnpja.com/office/{TAX_ID}"


def test_the_location_service_reaches_brasilapi_through_the_http_client_of_the_app() -> None:
    api = FakeApi(httpx2.Response(200, json=PAULISTA))

    response = client_with(api.client()).get("/cep/01310-200")

    assert response.json() == {"city": "São Paulo"}
    assert str(api.requests[0].url) == "https://brasilapi.com.br/api/cep/v2/01310200"


def test_an_invalid_cnpj_answers_422_before_any_request_is_made() -> None:
    response = client_with(no_network_client()).get("/cnpj/123")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {"detail": "O CNPJ informado é inválido."}


def test_an_unknown_cep_answers_404_with_the_message_in_portuguese() -> None:
    api = FakeApi(httpx2.Response(404, json=CEP_NOT_FOUND))

    response = client_with(api.client()).get("/cep/01310200")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Nenhum endereço encontrado para o CEP 01310200."}


def test_a_rate_limited_api_answers_503_and_asks_to_retry_later() -> None:
    api = FakeApi(httpx2.Response(429, text="Too Many Requests"))

    response = client_with(api.client()).get(f"/cnpj/{TAX_ID}")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.headers["retry-after"] == "60"
    assert response.json()["detail"].startswith("O limite de consultas")


def test_the_no_network_client_fails_loudly() -> None:
    client = client_with(no_network_client())

    with pytest.raises(AssertionError, match="must not reach an external API"):
        client.get(f"/cnpj/{TAX_ID}")
