import httpx2


class FakeApi:
    def __init__(self, response: httpx2.Response | Exception) -> None:
        self.response = response
        self.requests: list[httpx2.Request] = []

    def handle(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response

    def client(self, *, follow_redirects: bool = False) -> httpx2.Client:
        # No timeout here, so the tests prove the connectors set their own.
        transport = httpx2.MockTransport(self.handle)
        return httpx2.Client(transport=transport, timeout=None, follow_redirects=follow_redirects)


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        self.now += 1.0
        return self.now


def no_network_client() -> httpx2.Client:
    # Any request fails loudly, so no test can reach a real API by accident.
    return FakeApi(AssertionError("Tests must not reach an external API.")).client()
