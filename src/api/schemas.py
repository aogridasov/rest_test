from typing import Annotated, Optional, Union

import phonenumbers
from pydantic import BaseModel
from pydantic_extra_types.coordinate import Latitude, Longitude
from pydantic_extra_types.phone_numbers import PhoneNumberValidator

PhoneNumberType = Annotated[
    Union[str, phonenumbers.PhoneNumber],
    PhoneNumberValidator(default_region="RU", number_format="NATIONAL"),
]


class Base(BaseModel):

    pk: int

    class Config:
        orm_mode = True


class Building(Base):

    address: str
    lat: Latitude
    long: Longitude


class OperationType(Base):

    title: str
    parent_type: Optional["OperationType"] = None


class PhoneNumber(Base):

    number: PhoneNumberType | str


class Organization(Base):

    title: str
    phone_numbers: list[PhoneNumber]
    building: Building
    operation_types: list[OperationType]


class GeoPoint(BaseModel):
    latitude: Latitude
    longitude: Longitude
