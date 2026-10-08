class DomainError(Exception):
    pass


class UserAlreadyExistsError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"Já existe um usuário cadastrado com o e-mail {email}.")
