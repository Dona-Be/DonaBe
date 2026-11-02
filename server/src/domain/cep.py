import re

from src.domain.exceptions import InvalidCepError

CEP_PATTERN = re.compile(r"^([0-9]{5})-?([0-9]{3})$")
CEP_DIGITS = re.compile(r"^[0-9]{8}$")


def normalize_cep(cep: str) -> str:
    match = CEP_PATTERN.fullmatch(cep.strip())
    if match is None:
        raise InvalidCepError()
    return match.group(1) + match.group(2)
