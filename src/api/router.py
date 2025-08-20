from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy import select, text

from src.db.models import Building, OperationType, Organization

from . import schemas
from .dependencies import ApiKeyDep, DBSessionDep

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get(
    "/organizations/{pk}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.Organization,
    description="Получить информацию об организации по её идентификатору",
    dependencies=[ApiKeyDep],
)
async def get_organization(
    session: DBSessionDep,
    pk: int,
) -> list[schemas.Organization]:

    statement = select(Organization).filter_by(pk=pk)
    if org := await session.scalar(statement):
        return org
    raise HTTPException(status_code=404, detail="Организация не найдена")


@router.get(
    "/organizations",
    status_code=status.HTTP_200_OK,
    response_model=list[schemas.Organization],
    description=(
        "Список организаций, доступна фильтрация по зданию, "
        "виду деятельности. Доступен поиск по названию."
    ),
    dependencies=[ApiKeyDep],
)
async def get_organizations(
    session: DBSessionDep,
    building_pk: Optional[int] = Query(None, description="Фильтрация по зданию"),
    operation_type_pk: Optional[int] = Query(
        None, description="Фильтрация по типу деятельности"
    ),
    title_search: Optional[str] = Query(
        None, description="Частичное или полное название организации"
    ),
) -> list[schemas.Organization]:

    filters = []

    if building_pk:
        filters.append(Organization.building_pk == building_pk)

    if operation_type_pk:
        filters.append(
            Organization.operation_types.any(OperationType.pk.in_([operation_type_pk]))
        )

    if title_search:
        filters.append(Organization.title.icontains(title_search))

    statement = select(Organization).filter(*filters)
    return await session.scalars(statement)


@router.get(
    "/organizations_by_operation_type",
    status_code=status.HTTP_200_OK,
    response_model=list[schemas.Organization],
    description="Поиск организаций по названию вида деятельности",
    dependencies=[ApiKeyDep],
)
async def search_organizations_by_operation_type(
    session: DBSessionDep,
    type_title_search: Optional[str] = Query(
        None, description="Частичное или полное название вида деятельности"
    ),
) -> list[schemas.Organization]:

    statement = text(
        """
        WITH RECURSIVE r AS (
        SELECT ot.pk, ot.parent_type_pk, ot.title
        FROM operation_type ot
        WHERE title LIKE :val

        UNION ALL

        SELECT ot.pk, ot.parent_type_pk, ot.title
        FROM operation_type ot
        JOIN r ON ot.parent_type_pk = r.pk
        )

        SELECT
            org.pk
        FROM
            organization org
        LEFT JOIN organization_to_operation_type org_to_type
            ON org.pk = org_to_type.organization_pk
        JOIN r
            ON org_to_type.operation_type_pk = r.pk;
        """
    ).bindparams(
        val=f"%{type_title_search}%",
    )

    org_pks = await session.scalars(statement)
    org_pks = org_pks.all()

    if org_pks:
        statement = select(Organization).where(Organization.pk.in_(org_pks))
        return await session.scalars(statement)

    raise HTTPException(status_code=404, detail="Вид деятельности не найден")


@router.get(
    "/organizations_by_coordinates",
    status_code=status.HTTP_200_OK,
    response_model=list[schemas.Organization],
    description="Поиск организаций по заданной окружности на карте",
    dependencies=[ApiKeyDep],
)
async def search_organizations_by_coordinates(
    session: DBSessionDep,
    lat: Optional[float] = Query(None, description="Широта центра окружности"),
    lon: Optional[float] = Query(None, description="Долгота центра окружности"),
    radius_meters: Optional[int] = Query(
        100000,
        description="Радиус окружности, в метрах.",
    ),
) -> list[schemas.Organization]:

    try:
        parsed_coordinates = schemas.GeoPoint(latitude=lat, longitude=lon)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Некорректное значение координат")

    statement = text(
        """
        WITH close_buildings AS (
            SELECT *
            FROM building
            WHERE ST_DWithin(
                coordinates::geography,
                ST_SetSRID(ST_MakePoint(:lat, :lon), 4326)::geography,
                :radius
            )
        )

        SELECT
            org.pk
        FROM
            organization org
        JOIN close_buildings cb
            ON org.building_pk = cb.pk;
        """
    ).bindparams(
        lat=parsed_coordinates.latitude,
        lon=parsed_coordinates.longitude,
        radius=radius_meters,
    )

    org_pks = await session.scalars(statement)
    org_pks = org_pks.all()

    if org_pks:
        statement = select(Organization).where(Organization.pk.in_(org_pks))
        return await session.scalars(statement)

    raise HTTPException(status_code=404, detail="Организаций поблизости не найдено!")


@router.get(
    "/buildings",
    status_code=status.HTTP_200_OK,
    response_model=list[schemas.Building],
    description="Список зданий",
    dependencies=[ApiKeyDep],
)
async def get_buildings(session: DBSessionDep) -> list[schemas.Building]:

    statement = select(Building)
    return await session.scalars(statement)
