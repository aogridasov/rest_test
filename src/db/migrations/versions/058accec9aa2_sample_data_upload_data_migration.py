"""sample_data_upload_data_migration

Revision ID: 058accec9aa2
Revises: 5fbd82629c7f
Create Date: 2025-08-18 19:43:01.200801

"""

import json
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import Session

from src.db.models import (
    Building,
    OperationType,
    Organization,
    PhoneNumber,
    organization_to_operation_type_table,
)

revision: str = "058accec9aa2"
down_revision: Union[str, Sequence[str], None] = "5fbd82629c7f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = "5fbd82629c7f"


def upgrade():
    # Get a database session
    bind = op.get_bind()
    session = Session(bind=bind)

    # Load the JSON data
    with open(Path(__file__).parent.parent / "sample_data.json", "r") as f:
        data = json.load(f)

    # Process Operation Types (including hierarchy)
    operation_types_map = {}  # To store operation type titles to their PKs

    def process_operation_types(types_dict, parent_pk=None):
        for title, children in types_dict.items():
            # Create or get the operation type
            op_type = session.execute(
                sa.select(OperationType).where(OperationType.title == title)
            ).scalar_one_or_none()

            if op_type is None:
                op_type = OperationType(title=title, parent_type_pk=parent_pk)
                session.add(op_type)
                session.flush()  # To get the PK

            operation_types_map[title] = op_type.pk

            # Process children recursively
            if children:
                process_operation_types(children, op_type.pk)

    process_operation_types(data["Виды деятельности"])

    # Process Buildings
    buildings_map = {}  # To store building addresses to their PKs

    for address, coords in data["Здания"].items():
        building = session.execute(
            sa.select(Building).where(Building.address == address)
        ).scalar_one_or_none()

        if building is None:
            building = Building(address=address, lat=coords["lat"], long=coords["long"])
            session.add(building)
            session.flush()

        buildings_map[address] = building.pk

    # Process Organizations
    for org_data in data["Организации"]:
        # Get or create the organization
        org = session.execute(
            sa.select(Organization).where(Organization.title == org_data["title"])
        ).scalar_one_or_none()

        if org is None:
            building_pk = buildings_map[org_data["building"]]
            org = Organization(title=org_data["title"], building_pk=building_pk)
            session.add(org)
            session.flush()

            # Add phone numbers
            for number in org_data["phone_numbers"]:
                phone = PhoneNumber(number=number, organization_pk=org.pk)
                session.add(phone)

            # Add operation types
            for op_type_title in org_data["operation_types"]:
                op_type_pk = operation_types_map[op_type_title]
                stmt = sa.insert(organization_to_operation_type_table).values(
                    organization_pk=org.pk, operation_type_pk=op_type_pk
                )
                session.execute(stmt)

    session.commit()


def downgrade():
    # Get a database session
    bind = op.get_bind()
    session = Session(bind=bind)

    # Clear all data from the tables in reverse order of foreign key dependencies
    session.execute(sa.delete(organization_to_operation_type_table))
    session.execute(sa.delete(PhoneNumber.__table__))
    session.execute(sa.delete(Organization.__table__))
    session.execute(sa.delete(Building.__table__))

    # For OperationType, we need to clear the parent_type_pk references first
    session.execute(sa.update(OperationType.__table__).values(parent_type_pk=None))
    session.execute(sa.delete(OperationType.__table__))

    session.commit()
