from enum import Enum


class Metal(str, Enum):
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class Session(str, Enum):
    AM = "AM"
    PM = "PM"


class RateStatus(str, Enum):
    VALID = "valid"
    QUARANTINED = "quarantined"
    SUPERSEDED = "superseded"


class SchedulerMode(str, Enum):
    HOT = "HOT"
    CATCH_UP = "CATCH_UP"
    IDLE = "IDLE"
    OFF_DAY = "OFF_DAY"
