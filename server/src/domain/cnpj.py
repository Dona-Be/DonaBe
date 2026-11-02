import re

from src.domain.exceptions import InvalidCnpjError

# Since 2026 the CNPJ is alphanumeric; only the check digits stay numeric.
TAX_ID_PATTERN = re.compile(r"^[A-Z0-9]{12}[0-9]{2}$")
NOT_ALPHANUMERIC = re.compile(r"[^A-Za-z0-9]")
TAX_ID_BASE_LENGTH = 12
FIRST_DIGIT_WEIGHTS = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
SECOND_DIGIT_WEIGHTS = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
MODULUS = 11
LOWEST_REMAINDER_WITH_DIGIT = 2


def normalize_cnpj(cnpj: str) -> str:
    tax_id = NOT_ALPHANUMERIC.sub("", cnpj).upper()
    if not TAX_ID_PATTERN.fullmatch(tax_id):
        raise InvalidCnpjError()
    base = tax_id[:TAX_ID_BASE_LENGTH]
    if tax_id != base + check_digits(base):
        raise InvalidCnpjError()
    return tax_id


def check_digits(base: str) -> str:
    first = check_digit(base, FIRST_DIGIT_WEIGHTS)
    second = check_digit(base + first, SECOND_DIGIT_WEIGHTS)
    return first + second


def check_digit(characters: str, weights: list[int]) -> str:
    total = 0
    for character, weight in zip(characters, weights, strict=True):
        total += character_value(character) * weight
    remainder = total % MODULUS
    if remainder < LOWEST_REMAINDER_WITH_DIGIT:
        return "0"
    return str(MODULUS - remainder)


def character_value(character: str) -> int:
    # Receita rule: digits keep their value, letters count ASCII minus 48.
    return ord(character) - ord("0")
