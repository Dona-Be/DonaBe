import re

# fmt: off
VALID_AREA_CODES = frozenset({
    # Southeast
    11, 12, 13, 14, 15, 16, 17, 18, 19,
    21, 22, 24, 27, 28,
    31, 32, 33, 34, 35, 37, 38,
    # South
    41, 42, 43, 44, 45, 46, 47, 48, 49,
    51, 53, 54, 55,
    # Central-West
    61, 62, 64, 65, 66, 67,
    # Northeast
    71, 73, 74, 75, 77, 79,
    81, 82, 83, 84, 85, 86, 87, 88, 89,
    98, 99,
    # North
    63, 68, 69,
    91, 92, 93, 94, 95, 96, 97,
})
# fmt: on

CELLPHONE_PATTERN = re.compile(r"^([1-9]{2})9[0-9]{8}$")
LANDLINE_PATTERN = re.compile(r"^([1-9]{2})[2-5][0-9]{7}$")
PHONE_PATTERN = re.compile(r"^([1-9]{2})(?:9[0-9]{8}|[2-5][0-9]{7})$")
NOT_DIGIT = re.compile(r"[^0-9]")


def validate_cellphone(number: str) -> str:
    return validate_phone(number, CELLPHONE_PATTERN, "Não é um número de celular válido.")


def validate_landline(number: str) -> str:
    return validate_phone(number, LANDLINE_PATTERN, "Não é um número de telefone fixo válido.")


def validate_cellphone_or_landline(number: str) -> str:
    return validate_phone(number, PHONE_PATTERN, "Não é um número de telefone válido.")


def validate_phone(number: str, pattern: re.Pattern[str], error_message: str) -> str:
    # ValueError, so pydantic turns it into a 422 inside a field validator.
    digits = NOT_DIGIT.sub("", number)
    match = pattern.fullmatch(digits)
    if match is None:
        raise ValueError(error_message)
    area_code = match.group(1)
    if int(area_code) not in VALID_AREA_CODES:
        raise ValueError(f"O DDD {area_code} é inválido.")
    return digits
