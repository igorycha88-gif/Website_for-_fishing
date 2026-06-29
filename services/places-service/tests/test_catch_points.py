import pytest
from uuid import uuid4

from app.crud.catch_point import crud_catch_point
from app.models.catch_point import CatchPoint
from app.models.fish_type import FishType


async def _create_fish_type(db, name="Щука", category="predatory"):
    ft = FishType(name=name, icon="🐟", category=category, is_active=True)
    db.add(ft)
    await db.commit()
    await db.refresh(ft)
    return ft


@pytest.mark.asyncio
class TestCatchPointCRUD:
    async def test_create_and_get_catch_point(self, db):
        ft = await _create_fish_type(db, name="Щука-Test")
        cp = CatchPoint(
            latitude=56.8600,
            longitude=35.9200,
            fish_type_id=ft.id,
            river="volga",
            name="Верхняя Волга — Тверь",
            description="Закоряженные ямы",
            season=["summer", "autumn"],
            depth=3.5,
            bait="Воблер",
            weight_avg=2.1,
            is_demo=True,
            source_label="Демонстрационные данные",
            is_active=True,
        )
        db.add(cp)
        await db.commit()
        await db.refresh(cp)

        assert cp.id is not None
        assert cp.river == "volga"
        assert float(cp.latitude) == pytest.approx(56.86, abs=1e-4)

        result = await crud_catch_point.get(db, cp.id)
        assert result is not None
        assert result["fish_type"].name == "Щука-Test"
        assert result["river"] == "volga"

    async def test_get_nonexistent_returns_none(self, db):
        result = await crud_catch_point.get(db, uuid4())
        assert result is None

    async def test_list_filters_by_river(self, db):
        ft = await _create_fish_type(db, name="Судак-Test")
        for river in ("volga", "oka", "volga"):
            db.add(
                CatchPoint(
                    latitude=54.0,
                    longitude=39.0,
                    fish_type_id=ft.id,
                    river=river,
                    name=f"Точка {river}",
                    is_active=True,
                )
            )
        await db.commit()

        volga = await crud_catch_point.get_list(db, river="volga")
        oka = await crud_catch_point.get_list(db, river="oka")
        assert len(volga) == 2
        assert len(oka) == 1

        volga_count = await crud_catch_point.count(db, river="volga")
        assert volga_count == 2

    async def test_list_bbox_filter(self, db):
        ft = await _create_fish_type(db, name="Окунь-Test")
        db.add(
            CatchPoint(
                latitude=56.86, longitude=35.92, fish_type_id=ft.id,
                river="volga", name="Тверь", is_active=True,
            )
        )
        db.add(
            CatchPoint(
                latitude=55.79, longitude=49.12, fish_type_id=ft.id,
                river="volga", name="Казань", is_active=True,
            )
        )
        await db.commit()

        bbox = await crud_catch_point.get_list(
            db, min_lat=56.0, min_lon=35.0, max_lat=57.0, max_lon=36.0
        )
        assert len(bbox) == 1
        assert bbox[0]["name"] == "Тверь"

    async def test_list_filters_by_fish_type(self, db):
        ft1 = await _create_fish_type(db, name="Лещ-Test")
        ft2 = await _create_fish_type(db, name="Язь-Test")
        db.add(
            CatchPoint(
                latitude=54.5, longitude=36.2, fish_type_id=ft1.id,
                river="oka", name="Калуга-лещ", is_active=True,
            )
        )
        db.add(
            CatchPoint(
                latitude=54.6, longitude=36.3, fish_type_id=ft2.id,
                river="oka", name="Калуга-язь", is_active=True,
            )
        )
        await db.commit()

        res = await crud_catch_point.get_list(db, fish_type_id=ft1.id)
        assert len(res) == 1
        assert res[0]["fish_type"].name == "Лещ-Test"


@pytest.mark.asyncio
class TestCatchPointAPI:
    async def test_invalid_river_returns_400(self, db):
        from fastapi import HTTPException

        from app.endpoints.catches import get_catch_points

        with pytest.raises(HTTPException) as exc:
            await get_catch_points(river="moskva", db=db)
        assert exc.value.status_code == 400
