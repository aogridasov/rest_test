from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

organization_to_operation_type_table = Table(
    "organization_to_operation_type",
    Base.metadata,
    Column(
        "organization_pk",
        ForeignKey("organization.pk"),
        primary_key=True,
    ),
    Column(
        "operation_type_pk",
        ForeignKey("operation_type.pk"),
        primary_key=True,
    ),
)


class Organization(Base):

    __tablename__ = "organization"

    pk: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    phone_numbers: Mapped[list["PhoneNumber"]] = relationship(
        back_populates="organization",
        lazy="selectin",
    )

    building_pk: Mapped[int] = mapped_column(
        ForeignKey("building.pk"),
    )
    building: Mapped["Building"] = relationship(
        back_populates="organizations",
        lazy="selectin",
    )

    operation_types: Mapped[list["OperationType"]] = relationship(
        secondary=organization_to_operation_type_table,
        back_populates="organizations",
        lazy="selectin",
    )


class Building(Base):

    __tablename__ = "building"

    pk: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str]
    lat: Mapped[float]
    long: Mapped[float]

    organizations: Mapped[list["Organization"]] = relationship(
        back_populates="building",
        lazy="selectin",
    )


class PhoneNumber(Base):

    __tablename__ = "phone_number"

    pk: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str]
    organization_pk: Mapped[int] = mapped_column(ForeignKey("organization.pk"))
    organization: Mapped["Organization"] = relationship(
        back_populates="phone_numbers",
        lazy="selectin",
    )


class OperationType(Base):

    __tablename__ = "operation_type"

    pk: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]

    organizations: Mapped[list["Organization"]] = relationship(
        secondary=organization_to_operation_type_table,
        back_populates="operation_types",
        lazy="selectin",
    )

    parent_type_pk: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("operation_type.pk"),
        nullable=True,
    )
    child_types = relationship(
        "OperationType",
        back_populates="parent_type",
        lazy="joined",
        join_depth=3,
    )
    parent_type = relationship(
        "OperationType",
        back_populates="child_types",
        lazy="joined",
        remote_side=[pk],
        join_depth=3,
    )
