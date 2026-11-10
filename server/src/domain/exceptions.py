class DomainError(Exception):
    pass


class UserAlreadyExistsError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"Já existe um usuário cadastrado com o e-mail {email}.")


class InvalidCnpjError(DomainError):
    def __init__(self) -> None:
        super().__init__("O CNPJ informado é inválido.")


class CnpjNotFoundError(DomainError):
    def __init__(self, cnpj: str) -> None:
        super().__init__(f"Nenhuma empresa encontrada com o CNPJ {cnpj}.")


class UnsupportedLegalNatureError(DomainError):
    def __init__(self, legal_nature: str) -> None:
        super().__init__(
            f"Não é possível cadastrar instituições com a natureza jurídica {legal_nature}."
        )


class InvalidCepError(DomainError):
    def __init__(self) -> None:
        super().__init__("O CEP informado é inválido.")


class InvalidPhoneError(DomainError):
    def __init__(self) -> None:
        super().__init__("O telefone informado é inválido.")


class CepNotFoundError(DomainError):
    def __init__(self, cep: str) -> None:
        super().__init__(f"Nenhum endereço encontrado para o CEP {cep}.")


class CepWithoutCoordinatesError(DomainError):
    def __init__(self, cep: str) -> None:
        super().__init__(f"O CEP {cep} não tem uma localização conhecida.")


class RouteNotFoundError(DomainError):
    def __init__(self) -> None:
        super().__init__("Não foi possível traçar uma rota entre os dois endereços.")
