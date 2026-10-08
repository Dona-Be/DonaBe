from enum import StrEnum


class Role(StrEnum):
    DONOR = "donor"
    MANAGER = "manager"


class Cause(StrEnum):
    CHILDREN_AND_TEENAGERS = "children_and_teenagers"
    ELDERLY = "elderly"
    PEOPLE_WITH_DISABILITIES = "people_with_disabilities"
    HEALTH = "health"
    EDUCATION = "education"
    HUNGER_RELIEF = "hunger_relief"
    HOMELESS_PEOPLE = "homeless_people"
    WOMEN = "women"
    ANIMALS = "animals"
    ENVIRONMENT = "environment"


class Verdict(StrEnum):
    LIKELY_CHARITY = "likely_charity"
    NONPROFIT = "nonprofit"
    INACTIVE = "inactive"
    UNLIKELY = "unlikely"


class NeedType(StrEnum):
    ITEMS = "items"
    VOLUNTEERS = "volunteers"
    MONEY = "money"


class NeedStatus(StrEnum):
    OPEN = "open"
    FULFILLED = "fulfilled"
    CLOSED = "closed"


class DonationIntentStatus(StrEnum):
    REGISTERED = "registered"
    IN_CONTACT = "in_contact"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


ACTIVE_INTENT_STATUSES = frozenset(
    {DonationIntentStatus.REGISTERED, DonationIntentStatus.IN_CONTACT}
)
