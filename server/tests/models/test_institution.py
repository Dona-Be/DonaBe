import pytest
from sqlalchemy.exc import InvalidRequestError

from src.domain.enums import Cause, InstitutionType
from src.models.institution import Association, Foundation, Institution, ReligiousOrganization


def test_institution_itself_cannot_be_instantiated() -> None:
    with pytest.raises(InvalidRequestError, match="polymorphic_abstract"):
        Institution()


@pytest.mark.parametrize(
    ("subclass", "institution_type", "description", "causes"),
    [
        (
            Association,
            InstitutionType.ASSOCIATION,
            "Associação privada",
            (Cause.CHILDREN_AND_TEENAGERS, Cause.PEOPLE_WITH_DISABILITIES, Cause.ANIMALS),
        ),
        (
            Foundation,
            InstitutionType.FOUNDATION,
            "Fundação privada",
            (Cause.HEALTH, Cause.EDUCATION, Cause.ENVIRONMENT),
        ),
        (
            ReligiousOrganization,
            InstitutionType.RELIGIOUS_ORGANIZATION,
            "Organização religiosa",
            (Cause.HUNGER_RELIEF, Cause.HOMELESS_PEOPLE, Cause.ELDERLY),
        ),
    ],
)
def test_each_subclass_has_its_own_type_description_and_causes(
    subclass: type[Institution],
    institution_type: InstitutionType,
    description: str,
    causes: tuple[Cause, ...],
) -> None:
    institution = subclass()

    assert institution.type is institution_type
    assert institution.type_description == description
    assert institution.suggested_causes == causes
