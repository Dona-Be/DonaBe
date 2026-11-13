from fastapi import APIRouter, Response, status

from src.api.authentication import CurrentUser, NewUserProfile, ProfileOwner
from src.api.cookies import start_session
from src.api.dependencies import ProfileServiceDep, UserServiceDep
from src.domain.enums import Role
from src.domain.user_profile import UserProfile
from src.models.user import User
from src.schemas.profile import NewDonor, Profile, ProfileChanges

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post(
    "/donor",
    status_code=status.HTTP_201_CREATED,
    response_model=Profile,
    summary="Finish the signup as a donor",
    description="The CEP must have known coordinates. Starts the session.",
)
def create_donor(
    data: NewDonor, profile: NewUserProfile, service: ProfileServiceDep, response: Response
) -> User:
    donor = service.create_donor(profile, data.postal_code, data.preferred_causes)
    start_session(response, donor)
    return donor


@router.post(
    "/manager",
    status_code=status.HTTP_201_CREATED,
    response_model=Profile,
    summary="Finish the signup as a manager",
    description="Starts the session.",
)
def create_manager(profile: NewUserProfile, service: UserServiceDep, response: Response) -> User:
    manager = service.sign_up(profile, Role.MANAGER)
    start_session(response, manager)
    return manager


@router.get(
    "/me",
    response_model=Profile,
    summary="Read your own profile",
    description="The role is null while the signup is pending.",
)
def read_my_profile(owner: ProfileOwner) -> User | UserProfile:
    return owner


@router.patch("/me", response_model=Profile, summary="Edit your own profile")
def update_my_profile(
    changes: ProfileChanges, user: CurrentUser, service: ProfileServiceDep
) -> User:
    service.update(user, changes.model_dump(exclude_none=True))
    return user
