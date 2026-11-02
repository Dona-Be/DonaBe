from typing import Any

from src.connectors.schemas import Coordinates

# Real BrasilAPI answer on 2026-11-02.
PAULISTA: dict[str, Any] = {
    "cep": "01310200",
    "state": "SP",
    "city": "São Paulo",
    "neighborhood": "Bela Vista",
    "street": "Avenida Paulista",
    "service": "open-cep",
    "ibge": {"city": "3550308", "state": "35"},
    "timezoneName": "America/Sao_Paulo",
    "location": {
        "type": "Point",
        "coordinates": {"longitude": "-46.63611", "latitude": "-23.5475"},
    },
}
# BrasilAPI answer for the single CEP of a small town, only the fields read.
ACRELANDIA: dict[str, Any] = {
    "cep": "69945000",
    "state": "AC",
    "city": "Acrelândia",
    "neighborhood": None,
    "street": None,
    "location": {"coordinates": {"longitude": "-67.055", "latitude": "-10.07387"}},
}
CEP_INVALID: dict[str, Any] = {"name": "CepPromiseError", "type": "validation_error"}
CEP_NOT_FOUND: dict[str, Any] = {"name": "CepPromiseError", "type": "service_error"}

AACD_TAX_ID = "60979457000111"
# Real CNPJá answer (2026-11-02), cut to the fields read plus personal data.
AACD: dict[str, Any] = {
    "taxId": AACD_TAX_ID,
    "alias": "Aacd Ibirapuera",
    "company": {
        "name": "ASSOCIACAO DE ASSISTENCIA A CRIANCA DEFICIENTE",
        "nature": {"id": 3999, "text": "Associação Privada"},
        "members": [{"person": {"name": "Pessoa Física"}, "role": {"text": "Diretor"}}],
    },
    "status": {"id": 2, "text": "Ativa"},
    "address": {
        "street": "Avenida Prof Ascendino Reis",
        "number": "724",
        "district": "VL Clementino",
        "city": "São Paulo",
        "state": "SP",
        "details": None,
        "zip": "04027000",
    },
    "mainActivity": {"id": 8630501, "text": "Atividade médica ambulatorial"},
    "phones": [{"area": "11", "number": "50000000"}],
    "emails": [{"address": "contato@exemplo.org"}],
}
CNPJ_INVALID: dict[str, Any] = {"code": 400, "message": "request validation failed"}
CNPJ_NOT_FOUND: dict[str, Any] = {
    "code": 404,
    "message": "tax id not registered at revenue service",
}
CNPJ_RATE_LIMITED: dict[str, Any] = {"code": 429, "message": "rate limit exceeded"}

# Real OSRM answer between Praça da Sé and Avenida do Estado (2026-11-02).
PRACA_DA_SE = Coordinates(latitude=-23.550520, longitude=-46.633309)
AV_DO_ESTADO = Coordinates(latitude=-23.533773, longitude=-46.625290)
ROUTE_OK: dict[str, Any] = {"code": "Ok", "routes": [{"distance": 3570.3, "duration": 395.2}]}
