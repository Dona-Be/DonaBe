FULLWIDTH_ZERO = 0xFF10


def fullwidth(digits: str) -> str:
    # Fullwidth digits look like ASCII digits but are not.
    return "".join(chr(FULLWIDTH_ZERO + int(digit)) for digit in digits)
