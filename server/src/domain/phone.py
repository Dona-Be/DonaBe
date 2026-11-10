import re

from src.domain.exceptions import InvalidPhoneError

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

AREA_CODE = "([1-9]{2})"
CELLPHONE_NUMBER = "9[0-9]{8}"
LANDLINE_NUMBER = "[2-5][0-9]{7}"
CELLPHONE_PATTERN = re.compile(f"^{AREA_CODE}{CELLPHONE_NUMBER}$")
LANDLINE_PATTERN = re.compile(f"^{AREA_CODE}{LANDLINE_NUMBER}$")
PHONE_PATTERN = re.compile(f"^{AREA_CODE}(?:{CELLPHONE_NUMBER}|{LANDLINE_NUMBER})$")
NOT_DIGIT = re.compile(r"[^0-9]")


def validate_cellphone(number: str) -> str:
    return validate_phone(number, CELLPHONE_PATTERN)


def validate_landline(number: str) -> str:
    return validate_phone(number, LANDLINE_PATTERN)


def validate_cellphone_or_landline(number: str) -> str:
    return validate_phone(number, PHONE_PATTERN)


def validate_phone(number: str, pattern: re.Pattern[str]) -> str:
    digits = NOT_DIGIT.sub("", number)
    match = pattern.fullmatch(digits)
    if match is None or int(match.group(1)) not in VALID_AREA_CODES:
        raise InvalidPhoneError()
    return digits
