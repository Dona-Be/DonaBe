import time

import pytest
from fastapi.testclient import TestClient

from src.api.rate_limits import RateLimiter
from tests.api.helpers import DONOR_SIGNUP, GOOGLE_CALLBACK, sign_up
from tests.connectors.fakes import FakeClock

TOO_MANY_ATTEMPTS = {"detail": "Muitas tentativas. Tente novamente mais tarde."}


def test_attempts_over_the_limit_are_refused_for_that_key_only() -> None:
    limiter = RateLimiter(max_attempts=2, window_seconds=60)

    assert [limiter.count_attempt("maria") for _ in range(3)] == [True, True, False]
    assert limiter.count_attempt("joana")


def test_a_new_window_forgets_the_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    # Each attempt advances the fake clock by one second.
    monkeypatch.setattr(time, "monotonic", FakeClock().monotonic)
    limiter = RateLimiter(max_attempts=1, window_seconds=2)

    assert [limiter.count_attempt("maria") for _ in range(3)] == [True, False, True]


def test_profile_edits_over_the_limit_are_refused(client: TestClient) -> None:
    sign_up(client, "manager")

    statuses = [client.patch("/api/profiles/me", json={}).status_code for _ in range(21)]

    assert statuses == [200] * 20 + [429]
    assert client.patch("/api/profiles/me", json={}).json() == TOO_MANY_ATTEMPTS


def test_donor_signups_over_the_limit_are_refused(client: TestClient) -> None:
    client.get(GOOGLE_CALLBACK, follow_redirects=False)
    invalid = {**DONOR_SIGNUP, "postal_code": "0131020"}

    statuses = [client.post("/api/profiles/donor", json=invalid).status_code for _ in range(21)]

    assert statuses == [422] * 20 + [429]
    assert client.post("/api/profiles/donor", json=DONOR_SIGNUP).json() == TOO_MANY_ATTEMPTS
