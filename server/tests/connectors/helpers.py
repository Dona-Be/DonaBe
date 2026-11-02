from typing import Any

from tests.connectors.samples import AACD


def cnpja_payload(**changes: Any) -> dict[str, Any]:
    return {**AACD, **changes}


def cnpja_company_payload(**changes: Any) -> dict[str, Any]:
    return cnpja_payload(company={**AACD["company"], **changes})


def cnpja_address_payload(**changes: Any) -> dict[str, Any]:
    return cnpja_payload(address={**AACD["address"], **changes})
