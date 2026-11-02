EXTERNAL_SERVICE_MESSAGE = "Um serviço externo não respondeu. Tente novamente em alguns minutos."
RATE_LIMITED_MESSAGE = (
    "O limite de consultas a um serviço externo foi atingido. Tente novamente mais tarde."
)


class ExternalServiceError(Exception):
    user_message = EXTERNAL_SERVICE_MESSAGE

    def __init__(self, log_message: str) -> None:
        # The user reads user_message; log_message only goes to the server log.
        super().__init__(self.user_message)
        self.log_message = log_message


class RateLimitedError(ExternalServiceError):
    user_message = RATE_LIMITED_MESSAGE
