import json
import time
from http import HTTPStatus
from typing import Any

import httpx2

from src.connectors.exceptions import ExternalServiceError, RateLimitedError

DEFAULT_TIMEOUT = 5.0
MAX_BODY_BYTES = 1_000_000

http_client = httpx2.Client(timeout=DEFAULT_TIMEOUT)


def get_bytes(client: httpx2.Client, url: str, service: str) -> tuple[int, bytes]:
    deadline = time.monotonic() + DEFAULT_TIMEOUT
    try:
        # Redirects could send the request to an internal host.
        with client.stream("GET", url, timeout=DEFAULT_TIMEOUT, follow_redirects=False) as response:
            raise_for_rate_limit(response.status_code, service)
            return response.status_code, read_body(response, deadline, service)
    except httpx2.HTTPError as error:
        raise ExternalServiceError(f"{service} request failed") from error


def raise_for_rate_limit(status_code: int, service: str) -> None:
    # Every API answers 429 when the quota shared by our server runs out.
    if status_code == HTTPStatus.TOO_MANY_REQUESTS:
        raise RateLimitedError(f"{service} rate limit reached")


def read_body(response: httpx2.Response, deadline: float, service: str) -> bytes:
    # The httpx timeout is per read, so the whole body also gets a deadline.
    body = bytearray()
    for chunk in response.iter_bytes():
        body += chunk
        if len(body) > MAX_BODY_BYTES:
            raise ExternalServiceError(f"{service} sent a body over {MAX_BODY_BYTES} bytes")
        if time.monotonic() > deadline:
            raise ExternalServiceError(f"{service} took longer than the deadline")
    return bytes(body)


def parse_json(body: bytes, service: str) -> dict[str, Any]:
    try:
        data = json.loads(body, parse_constant=reject_constant)
    except (ValueError, RecursionError) as error:
        raise ExternalServiceError(f"{service} sent invalid JSON") from error
    if not isinstance(data, dict):
        raise ExternalServiceError(f"{service} sent a JSON body that is not an object")
    return data


def reject_constant(name: str) -> None:
    # NaN and Infinity are Python extensions, not JSON.
    raise ValueError(f"{name} is not JSON")
