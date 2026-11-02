from dataclasses import dataclass

from src.connectors.companies import CompanyLookup
from src.connectors.schemas import Company
from src.domain.charity import CharityClassifier, Classification
from src.domain.cnpj import normalize_cnpj


@dataclass(frozen=True)
class ClassifiedCompany:
    company: Company
    classification: Classification


class CnpjService:
    def __init__(self, companies: CompanyLookup) -> None:
        self._companies = companies
        self._classifier = CharityClassifier()

    def classify(self, cnpj: str) -> ClassifiedCompany:
        tax_id = normalize_cnpj(cnpj)
        company = self._companies.get_company(tax_id)
        classification = self._classifier.classify(company.registry_data())
        return ClassifiedCompany(company, classification)
