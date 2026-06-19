from __future__ import annotations
from enum import IntEnum


class GaitMode(IntEnum):
    WALKING = (1, "Walking")
    STAIR_ASCENT = (2, "Stair Ascent")
    STANDING = (3, "Standing")
    STAIR_DESCENT = (4, "Stair Descent")
    UPSLOPE_WALKING = (5, "Upslope Walking")
    DOWNSLOPE_WALKING = (6, "Downslope Walking")
    SITTING = (7, "Sitting")
    SIT_TO_STAND = (8, "Sit to Stand")
    STAND_TO_SIT = (9, "Stand to Sit")

    label: str

    def __new__(cls, value: int, label: str) -> GaitMode:
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.label = label
        return obj

    @staticmethod
    def parse_mode(value: int) -> GaitMode | None:
        try:
            return GaitMode(value)
        except ValueError:
            return None
