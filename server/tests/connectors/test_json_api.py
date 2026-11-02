import gzip
import time
from collections.abc import Iterator

import httpx2
import pytest

from src.connectors.exceptions import ExternalServiceError, RateLimitedError
from src.connectors.json_api import DEFAULT_TIMEOUT, MAX_BODY_BYTES, get_bytes, parse_json
from tests.connectors.fakes import FakeApi, FakeClock

URL = "https://api.exemplo/recurso"
SERVICE = "Exemplo"
GZIP_HEADERS = {"Content-Encoding": "gzip"}


def test_get_bytes_returns_the_status_and_the_body() -> None:
    api = FakeApi(httpx2.Response(200, content=b'{"ok": true}'))

    assert get_bytes(api.client(), URL, SERVICE) == (200, b'{"ok": true}')


def test_get_bytes_sets_the_default_timeout_on_the_request() -> None:
    api = FakeApi(httpx2.Response(200, content=b"{}"))

    get_bytes(api.client(), URL, SERVICE)

    assert api.requests[0].extensions["timeout"] == httpx2.Timeout(DEFAULT_TIMEOUT).as_dict()


def test_get_bytes_joins_the_chunks_of_the_body() -> None:
    api = FakeApi(httpx2.Response(200, content=iter([b'{"a"', b": 1}"])))

    assert get_bytes(api.client(), URL, SERVICE) == (200, b'{"a": 1}')


def test_get_bytes_returns_a_redirect_without_following_it() -> None:
    redirect = httpx2.Response(302, content=b"{}", headers={"Location": "http://10.0.0.1/"})
    api = FakeApi(redirect)

    status_code, _ = get_bytes(api.client(follow_redirects=True), URL, SERVICE)

    assert status_code == 302
    assert len(api.requests) == 1


@pytest.mark.parametrize(
    "body", [b"Too Many Requests", b'{"message": "rate limit exceeded"}'], ids=["text", "json"]
)
def test_get_bytes_reports_a_rate_limit_whatever_the_body(body: bytes) -> None:
    client = FakeApi(httpx2.Response(429, content=body)).client()

    with pytest.raises(RateLimitedError) as caught:
        get_bytes(client, URL, SERVICE)

    assert caught.value.log_message == "Exemplo rate limit reached"


def test_get_bytes_accepts_a_body_at_the_size_limit() -> None:
    api = FakeApi(httpx2.Response(200, content=b"x" * MAX_BODY_BYTES))

    _, body = get_bytes(api.client(), URL, SERVICE)

    assert len(body) == MAX_BODY_BYTES


@pytest.mark.parametrize(
    ("content", "headers"),
    [
        (b"x" * (MAX_BODY_BYTES + 1), {}),
        (iter([b"x" * MAX_BODY_BYTES, b"x"]), {}),
        (iter([gzip.compress(b"x" * (MAX_BODY_BYTES + 1))]), GZIP_HEADERS),
    ],
    ids=["one body", "chunks", "compressed stream"],
)
def test_get_bytes_rejects_a_body_over_the_size_limit(
    content: object, headers: dict[str, str]
) -> None:
    client = FakeApi(httpx2.Response(200, content=content, headers=headers)).client()

    with pytest.raises(ExternalServiceError) as caught:
        get_bytes(client, URL, SERVICE)

    assert caught.value.log_message == f"Exemplo sent a body over {MAX_BODY_BYTES} bytes"


def test_get_bytes_checks_the_deadline_on_every_chunk(monkeypatch: pytest.MonkeyPatch) -> None:
    # Each clock reading adds one second, so the deadline passes mid-body.
    clock = FakeClock()
    monkeypatch.setattr(time, "monotonic", clock.monotonic)
    sent: list[bytes] = []

    def body() -> Iterator[bytes]:
        for chunk in [b" "] * 20:
            sent.append(chunk)
            yield chunk

    client = FakeApi(httpx2.Response(200, content=body())).client()

    with pytest.raises(ExternalServiceError) as caught:
        get_bytes(client, URL, SERVICE)

    assert caught.value.log_message == "Exemplo took longer than the deadline"
    assert len(sent) == int(DEFAULT_TIMEOUT) + 1


def test_get_bytes_keeps_the_transport_error_as_the_cause() -> None:
    client = FakeApi(httpx2.ReadTimeout("slow")).client()

    with pytest.raises(ExternalServiceError) as caught:
        get_bytes(client, URL, SERVICE)

    assert caught.value.log_message == "Exemplo request failed"
    assert isinstance(caught.value.__cause__, httpx2.ReadTimeout)


def test_get_bytes_maps_a_failure_in_the_middle_of_the_body() -> None:
    def body() -> Iterator[bytes]:
        yield b'{"a"'
        raise httpx2.ReadError("connection lost")

    client = FakeApi(httpx2.Response(200, content=body())).client()

    with pytest.raises(ExternalServiceError) as caught:
        get_bytes(client, URL, SERVICE)

    assert caught.value.log_message == "Exemplo request failed"
    assert isinstance(caught.value.__cause__, httpx2.ReadError)


def test_parse_json_returns_the_object() -> None:
    assert parse_json(b'{"a": 1}', SERVICE) == {"a": 1}


@pytest.mark.parametrize(
    "body",
    [
        b"Too Many Requests",
        "Requisições demais".encode("latin-1"),
        b"[1, 2]",
        b"[" * 100_000 + b"]" * 100_000,
        b'{"a": NaN}',
        b'{"a": -Infinity}',
    ],
    ids=["text", "latin-1 text", "list", "deeply nested", "nan", "infinity"],
)
def test_parse_json_rejects_bodies_that_are_not_a_json_object(body: bytes) -> None:
    with pytest.raises(ExternalServiceError):
        parse_json(body, SERVICE)


def test_parse_json_keeps_the_decoding_error_as_the_cause() -> None:
    with pytest.raises(ExternalServiceError) as caught:
        parse_json(b"not json", SERVICE)

    assert caught.value.log_message == "Exemplo sent invalid JSON"
    assert isinstance(caught.value.__cause__, ValueError)
