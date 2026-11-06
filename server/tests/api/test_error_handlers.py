import json

import pytest
from fastapi import Request, status

from src.api.error_handlers import respond_with_error, status_for
from src.connectors.exceptions import ExternalServiceError, RateLimitedError
from src.domain.exceptions import CnpjNotFoundError, DomainError, UserAlreadyExistsError

REQUEST = Request(
    {"type": "http", "method": "GET", "path": "/", "headers": [], "query_string": b""}
)
EXTERNAL_FAILURE_MESSAGE = "Um serviço externo não respondeu. Tente novamente em alguns minutos."


class ConcurrentSignupError(UserAlreadyExistsError):
    pass


class NewRuleError(DomainError):
    def __init__(self) -> None:
        super().__init__("Uma regra nova foi violada.")


def body_of(response_body: bytes | memoryview) -> dict[str, str]:
    return json.loads(bytes(response_body))


def test_a_subclass_of_a_mapped_error_gets_the_same_status() -> None:
    assert status_for(ConcurrentSignupError("maria@exemplo.com")) == status.HTTP_409_CONFLICT


def test_an_unmapped_error_is_a_server_error() -> None:
    assert status_for(RuntimeError("boom")) == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_a_domain_error_answers_with_its_own_message() -> None:
    response = respond_with_error(REQUEST, CnpjNotFoundError("00000000000191"))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert body_of(response.body) == {
        "detail": "Nenhuma empresa encontrada com o CNPJ 00000000000191."
    }


def test_a_domain_error_without_its_own_status_is_a_bad_request() -> None:
    response = respond_with_error(REQUEST, NewRuleError())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert body_of(response.body) == {"detail": "Uma regra nova foi violada."}


def test_an_external_failure_logs_the_detail_and_hides_it_from_the_user(
    caplog: pytest.LogCaptureFixture,
) -> None:
    response = respond_with_error(REQUEST, ExternalServiceError("CNPJá answered HTTP 500"))

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.headers["retry-after"] == "60"
    assert body_of(response.body) == {"detail": EXTERNAL_FAILURE_MESSAGE}
    assert "CNPJá answered HTTP 500" in caplog.text
    assert EXTERNAL_FAILURE_MESSAGE not in caplog.text


def test_the_cause_of_an_external_failure_is_logged_on_one_line(
    caplog: pytest.LogCaptureFixture,
) -> None:
    error = ExternalServiceError("BrasilAPI sent invalid JSON")
    error.__cause__ = ValueError("forged\nINFO: fake line")

    respond_with_error(REQUEST, error)

    assert "'BrasilAPI sent invalid JSON': ValueError 'forged\\nINFO: fake line'" in caplog.text
    assert "\nINFO: fake line" not in caplog.text


def test_a_forged_newline_in_the_log_message_stays_on_one_line(
    caplog: pytest.LogCaptureFixture,
) -> None:
    respond_with_error(REQUEST, ExternalServiceError("OSRM answered\nINFO: fake line"))

    assert "'OSRM answered\\nINFO: fake line'" in caplog.text
    assert "\nINFO: fake line" not in caplog.text


def test_a_long_log_message_is_cut(caplog: pytest.LogCaptureFixture) -> None:
    respond_with_error(REQUEST, ExternalServiceError("x" * 1000))

    assert "x" * 200 in caplog.text
    assert "x" * 201 not in caplog.text


def test_a_long_cause_is_cut_too(caplog: pytest.LogCaptureFixture) -> None:
    error = ExternalServiceError("CNPJá sent an unexpected body")
    error.__cause__ = ValueError("y" * 1000)

    respond_with_error(REQUEST, error)

    assert "y" * 200 in caplog.text
    assert "y" * 201 not in caplog.text


def test_a_rate_limit_asks_the_client_to_retry_later() -> None:
    response = respond_with_error(REQUEST, RateLimitedError("CNPJá rate limit reached"))

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.headers["retry-after"] == "60"
    assert body_of(response.body)["detail"].startswith("O limite de consultas")
