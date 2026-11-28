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
        super().__init__(f"O CEP {cep} não tem uma localização conhecida. Informe um CEP próximo.")


class RouteNotFoundError(DomainError):
    def __init__(self) -> None:
        super().__init__("Não foi possível traçar uma rota entre os dois endereços.")


class FieldNotInProfileError(DomainError):
    def __init__(self, field: str) -> None:
        super().__init__(f"O campo {field} não faz parte do seu perfil.")


class InvalidTransitionError(DomainError):
    def __init__(self) -> None:
        super().__init__("Não é possível fazer essa mudança de status na intenção de doação.")


class NotificationNotFoundError(DomainError):
    def __init__(self) -> None:
        super().__init__("Notificação não encontrada.")


class InstitutionAlreadyExistsError(DomainError):
    def __init__(self, cnpj: str) -> None:
        super().__init__(f"Já existe uma instituição cadastrada com o CNPJ {cnpj}.")


class InactiveCnpjError(DomainError):
    def __init__(self) -> None:
        super().__init__("Não é possível cadastrar um CNPJ que não está ativo.")


class IncompleteAddressError(DomainError):
    def __init__(self) -> None:
        super().__init__("O endereço do CNPJ está incompleto. Informe rua, número, bairro e CEP.")


class InstitutionNotFoundError(DomainError):
    def __init__(self) -> None:
        super().__init__("Instituição não encontrada.")


class NotInstitutionManagerError(DomainError):
    def __init__(self) -> None:
        super().__init__("Apenas o gestor da instituição pode editá-la.")


class NeedNotFoundError(DomainError):
    def __init__(self) -> None:
        super().__init__("Necessidade não encontrada.")


class NotNeedManagerError(DomainError):
    def __init__(self) -> None:
        super().__init__("Apenas o gestor da instituição pode alterar esta necessidade.")


class NeedNotOpenError(DomainError):
    def __init__(self) -> None:
        super().__init__("Apenas necessidades abertas podem mudar de status.")


class InvalidSearchStrategyError(DomainError):
    def __init__(self, strategy: str) -> None:
        super().__init__(f"A estratégia de busca {strategy} não é válida.")


class DonorWithoutLocationError(DomainError):
    def __init__(self) -> None:
        super().__init__("Informe seu CEP no perfil para buscar instituições perto de você.")
