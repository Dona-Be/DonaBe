from typing import Any

import httpx2

from src.connectors.addresses import BrasilApiAddressLookup
from src.connectors.companies import CnpjaCompanyLookup
from tests.connectors.fakes import FakeApi
from tests.connectors.samples import AACD


def address_lookup_with(
    response: httpx2.Response | Exception, **options: str
) -> tuple[BrasilApiAddressLookup, FakeApi]:
    api = FakeApi(response)
    return BrasilApiAddressLookup(api.client(), **options), api


def company_lookup_with(
    response: httpx2.Response | Exception, **options: str
) -> tuple[CnpjaCompanyLookup, FakeApi]:
    api = FakeApi(response)
    return CnpjaCompanyLookup(api.client(), **options), api


def cnpja_payload(**changes: Any) -> dict[str, Any]:
    return {**AACD, **changes}


def cnpja_company_payload(**changes: Any) -> dict[str, Any]:
    return cnpja_payload(company={**AACD["company"], **changes})


def cnpja_address_payload(**changes: Any) -> dict[str, Any]:
    return cnpja_payload(address={**AACD["address"], **changes})
