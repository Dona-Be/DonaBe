from collections.abc import Generator
from typing import Annotated

import httpx2
from fastapi import Depends
from sqlalchemy.orm import Session

from src.auth.google import GoogleClient, google_client
from src.connectors.addresses import AddressLookup, BrasilApiAddressLookup
from src.connectors.companies import CnpjaCompanyLookup, CompanyLookup
from src.connectors.json_api import http_client
from src.connectors.routing import OsrmRoutePlanner, RoutePlanner
from src.core.database import engine
from src.repositories.institutions import InstitutionRepository, SqlAlchemyInstitutionRepository
from src.repositories.needs import NeedRepository, SqlAlchemyNeedRepository
from src.repositories.notifications import NotificationRepository, SqlAlchemyNotificationRepository
from src.repositories.users import SqlAlchemyUserRepository, UserRepository
from src.services.cnpj import CnpjService
from src.services.institutions import InstitutionService
from src.services.intent_events import (
    DonorNotificationObserver,
    IntentEventPublisher,
    ManagerNotificationObserver,
)
from src.services.locations import LocationService
from src.services.needs import NeedService
from src.services.notifications import NotificationService
from src.services.profiles import ProfileService
from src.services.search_strategies import InstitutionSearchService
from src.services.users import UserService


def get_db_session() -> Generator[Session]:
    with Session(engine, expire_on_commit=False) as session:
        yield session


def get_google_client() -> GoogleClient:
    return google_client


GoogleClientDep = Annotated[GoogleClient, Depends(get_google_client)]


def get_http_client() -> httpx2.Client:
    return http_client


HttpClientDep = Annotated[httpx2.Client, Depends(get_http_client)]


def get_user_repository(session: Annotated[Session, Depends(get_db_session)]) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repository)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_company_lookup(client: HttpClientDep) -> CompanyLookup:
    return CnpjaCompanyLookup(client)


def get_address_lookup(client: HttpClientDep) -> AddressLookup:
    return BrasilApiAddressLookup(client)


def get_route_planner(client: HttpClientDep) -> RoutePlanner:
    return OsrmRoutePlanner(client)


def get_cnpj_service(
    companies: Annotated[CompanyLookup, Depends(get_company_lookup)],
) -> CnpjService:
    return CnpjService(companies)


CnpjServiceDep = Annotated[CnpjService, Depends(get_cnpj_service)]


def get_location_service(
    addresses: Annotated[AddressLookup, Depends(get_address_lookup)],
    routes: Annotated[RoutePlanner, Depends(get_route_planner)],
) -> LocationService:
    return LocationService(addresses, routes)


LocationServiceDep = Annotated[LocationService, Depends(get_location_service)]


def get_profile_service(
    users: UserServiceDep,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    locations: LocationServiceDep,
) -> ProfileService:
    return ProfileService(users, repository, locations)


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]


def get_institution_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> InstitutionRepository:
    return SqlAlchemyInstitutionRepository(session)


def get_institution_service(
    repository: Annotated[InstitutionRepository, Depends(get_institution_repository)],
    cnpj: CnpjServiceDep,
    locations: LocationServiceDep,
) -> InstitutionService:
    return InstitutionService(repository, cnpj, locations)


InstitutionServiceDep = Annotated[InstitutionService, Depends(get_institution_service)]


def get_institution_search_service(
    repository: Annotated[InstitutionRepository, Depends(get_institution_repository)],
) -> InstitutionSearchService:
    return InstitutionSearchService(repository)


InstitutionSearchServiceDep = Annotated[
    InstitutionSearchService, Depends(get_institution_search_service)
]


def get_need_repository(session: Annotated[Session, Depends(get_db_session)]) -> NeedRepository:
    return SqlAlchemyNeedRepository(session)


def get_need_service(
    repository: Annotated[NeedRepository, Depends(get_need_repository)],
    institutions: Annotated[InstitutionRepository, Depends(get_institution_repository)],
) -> NeedService:
    return NeedService(repository, institutions)


NeedServiceDep = Annotated[NeedService, Depends(get_need_service)]


def get_notification_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> NotificationRepository:
    return SqlAlchemyNotificationRepository(session)


def get_notification_service(
    repository: Annotated[NotificationRepository, Depends(get_notification_repository)],
) -> NotificationService:
    return NotificationService(repository)


NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]


def get_intent_event_publisher(
    notifications: Annotated[NotificationRepository, Depends(get_notification_repository)],
) -> IntentEventPublisher:
    publisher = IntentEventPublisher()
    publisher.attach(ManagerNotificationObserver(notifications))
    publisher.attach(DonorNotificationObserver(notifications))
    return publisher
