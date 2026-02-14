import pytest
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, text, select
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime, date
from decimal import Decimal

from app.core.config import settings
from app.models.fish_type import FishType
from app.models.equipment_type import EquipmentType
from app.models.favorite_place import FavoritePlace
from app.models.place import Place
from app.core.database import Base


@pytest.fixture
async def db():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    testing_async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with testing_async_session() as session:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Clean ONLY places service related data - DO NOT CLEAN users!
        await session.execute(text("DELETE FROM favorite_places"))
        await session.execute(text("DELETE FROM fish_types"))
        await session.execute(text("DELETE FROM equipment_types"))
        await session.execute(text("DELETE FROM places"))
        await session.commit()

        yield session


@pytest.mark.asyncio
class TestFishType:
    async def test_create_fish_type(self, db: AsyncSession):
        fish_type_data = {
            "name": "Щука",
            "icon": "🐟",
            "category": "predatory",
            "is_active": True,
        }

        fish_type = FishType(**fish_type_data)
        db.add(fish_type)
        await db.commit()
        await db.refresh(fish_type)

        assert fish_type.id is not None
        assert fish_type.name == "Щука"
        assert fish_type.icon == "🐟"
        assert fish_type.category == "predatory"
        assert fish_type.is_active is True

        assert fish_type.created_at is not None
        assert fish_type.updated_at is not None

    async def test_get_fish_type(self, db: AsyncSession):
        fish_type_data = {
            "name": "Судак",
            "icon": "🐟",
            "category": "predatory",
            "is_active": True,
        }

        fish_type = FishType(**fish_type_data)
        db.add(fish_type)
        await db.commit()

        result = await db.get(FishType, fish_type.id)

        assert result is not None
        assert result.id == fish_type.id

    async def test_get_all_fish_types(self, db: AsyncSession):
        for fish_type_name in ["Щука", "Судак", "Окунь", "Налим"]:
            fish_type = FishType(
                name=fish_type_name, icon="🐟", category="predatory", is_active=True
            )
            db.add(fish_type)
        await db.commit()

        results = await db.execute(select(FishType))
        fish_types = results.scalars().all()

        assert len(fish_types) == 4
        assert len(fish_types) > 0

    async def test_update_fish_type(self, db: AsyncSession):
        fish_type = FishType(
            name="Карась",
            icon="🐠",
            category="peaceful",
            is_active=True,
        )
        db.add(fish_type)
        await db.commit()
        await db.refresh(fish_type)

        updated_data = {
            "name": "Карась (обновленный)",
            "icon": "🐠",
            "category": "peaceful",
            "is_active": False,
        }

        from app.crud.fish_type import crud_fish_type as crud

        result = await crud.update(
            db=db, fish_type_id=fish_type.id, fish_type_in=updated_data
        )

        assert result is not None
        assert result.name == "Карась (обновленный)"
        assert result.is_active is False

    async def test_delete_fish_type(self, db: AsyncSession):
        fish_type = FishType(
            name="Сазан",
            icon="🐟",
            category="peaceful",
            is_active=True,
        )
        db.add(fish_type)
        await db.commit()
        fish_type_id = fish_type.id

        from app.crud.fish_type import crud_fish_type as crud

        result = await crud.delete(db=db, fish_type_id=fish_type_id)

        assert result is True

        result = await crud.get(db=db, fish_type_id=fish_type_id)
        assert result is None


@pytest.mark.asyncio
class TestEquipmentType:
    async def test_create_equipment_type(self, db: AsyncSession):
        equipment_type_data = {
            "name": "Спиннинг",
            "category": "rod",
            "is_active": True,
        }

        equipment_type = EquipmentType(**equipment_type_data)
        db.add(equipment_type)
        await db.commit()
        await db.refresh(equipment_type)

        assert equipment_type.id is not None
        assert equipment_type.name == "Спиннинг"
        assert equipment_type.category == "rod"
        assert equipment_type.is_active is True

    async def test_get_all_equipment_types(self, db: AsyncSession):
        for equipment_data in [
            {"name": "Спиннинг", "category": "rod"},
            {"name": "Фидер", "category": "rod"},
            {"name": "Поплавочная", "category": "rod"},
        ]:
            equipment_type = EquipmentType(**equipment_data)
            db.add(equipment_type)
        await db.commit()

        results = await db.execute(select(EquipmentType))
        equipment_types = results.scalars().all()

        assert len(equipment_types) == 3
        assert len(equipment_types) > 0

    async def test_update_equipment_type(self, db: AsyncSession):
        equipment_type = EquipmentType(
            name="Спиннинг",
            category="rod",
            is_active=True,
        )
        db.add(equipment_type)
        await db.commit()
        await db.refresh(equipment_type)

        updated_data = {
            "name": "Спиннинг (обновленный)",
            "category": "reel",
            "is_active": False,
        }

        from app.crud.equipment_type import crud_equipment_type as crud

        result = await crud.update(
            db=db, equipment_type_id=equipment_type.id, equipment_type_in=updated_data
        )

        assert result is not None
        assert result.name == "Спиннинг (обновленный)"
        assert result.category == "reel"
        assert result.is_active is False

    async def test_delete_equipment_type(self, db: AsyncSession):
        equipment_type = EquipmentType(
            name="Поплавочная",
            category="rod",
            is_active=True,
        )
        db.add(equipment_type)
        await db.commit()
        equipment_type_id = equipment_type.id

        from app.crud.equipment_type import crud_equipment_type as crud

        result = await crud.delete(db=db, equipment_type_id=equipment_type_id)

        assert result is True

        result = await crud.get(db=db, equipment_type_id=equipment_type_id)
        assert result is None


@pytest.mark.asyncio
class TestFavoritePlace:
    async def test_add_to_favorites(self, db: AsyncSession):
        user_id = uuid4()
        place_id = uuid4()

        favorite = FavoritePlace(user_id=user_id, place_id=place_id)
        db.add(favorite)
        await db.commit()
        await db.refresh(favorite)

        assert favorite.id is not None
        assert favorite.user_id == user_id
        assert favorite.place_id == place_id

    async def test_remove_from_favorites(self, db: AsyncSession):
        user_id = uuid4()
        place_id = uuid4()

        favorite = FavoritePlace(user_id=user_id, place_id=place_id)
        db.add(favorite)
        await db.commit()
        await db.refresh(favorite)
        favorite_id = favorite.id

        result = await db.execute(
            select(FavoritePlace).where(
                FavoritePlace.user_id == user_id, FavoritePlace.place_id == place_id
            )
        )
        result = result.scalar_one_or_none()

        assert result is not None

        from app.crud.favorite_place import crud_favorite_place as crud

        delete_result = await crud.delete(db=db, user_id=user_id, place_id=place_id)

        assert delete_result is True

        result = await db.execute(
            select(FavoritePlace).where(
                FavoritePlace.user_id == user_id, FavoritePlace.place_id == place_id
            )
        )
        result = result.scalar_one_or_none()

        assert result is None

    async def test_get_favorites_by_user(self, db: AsyncSession):
        user_id = uuid4()
        place_id1 = uuid4()
        place_id2 = uuid4()

        for place_id in [place_id1, place_id2]:
            favorite = FavoritePlace(user_id=user_id, place_id=place_id)
            db.add(favorite)
            await db.commit()

        from app.crud.favorite_place import crud_favorite_place as crud

        results = await crud.get_by_user(db=db, user_id=user_id)

        assert len(results) == 2
        assert all(f.user_id == user_id)


@pytest.mark.asyncio
class TestPlace:
    async def test_create_place(self, db: AsyncSession):
        user_id = uuid4()

        place_data = {
            "name": "Озеро Рыбное",
            "description": "Красивое озеро в лесу",
            "latitude": 55.75,
            "longitude": 37.61,
            "address": "г. Москва, Example",
            "place_type": "wild",
            "access_type": "car",
            "fish_types": [str(uuid4()), str(uuid4())],
            "seasonality": ["summer", "autumn"],
            "visibility": "private",
            "images": [
                "http://example.com/photo1.jpg",
                "http://example.com/photo2.jpg",
            ],
        }

        place = Place(owner_id=user_id, **place_data)
        db.add(place)
        await db.commit()
        await db.refresh(place)

        assert place.id is not None
        assert place.name == "Озеро Рыбное"
        assert place.visibility == "private"
        assert len(place.images) == 2

    async def test_get_place(self, db: AsyncSession):
        user_id = uuid4()

        place_data = {
            "name": "Озеро Рыбное",
            "description": "Красивое озеро в лесу",
            "latitude": 55.75,
            "longitude": 37.61,
            "address": "г. Москва, Example",
            "place_type": "wild",
            "access_type": "car",
            "fish_types": [str(uuid4()), str(uuid4())],
            "seasonality": ["summer", "autumn"],
            "visibility": "private",
            "images": ["http://example.com/photo1.jpg"],
        }

        place = Place(owner_id=user_id, **place_data)
        db.add(place)
        await db.commit()
        await db.refresh(place)

        result = await db.get(Place, place.id)

        assert result is not None
        assert result.id == place.id
        assert result.owner_id == user_id

    async def test_get_places_by_user(self, db: AsyncSession):
        user_id = uuid4()

        for i in range(3):
            place_data = {
                "name": f"Место {i}",
                "latitude": 55.75 + i * 0.01,
                "longitude": 37.61 + i * 0.01,
                "address": f"Адрес {i}",
                "place_type": "wild",
                "access_type": "car",
                "fish_types": [str(uuid4()), str(uuid4())],
                "seasonality": ["summer", "autumn"],
                "visibility": "private",
                "images": [],
            }
            place = Place(owner_id=user_id, **place_data)
            db.add(place)
            await db.commit()

        from app.crud.place import crud_place as crud

        results = await crud.get_by_user(db=db, user_id=user_id, page=1, page_size=20)

        assert results.total == 3
        assert len(results.places) == 3
        assert all(p.owner_id == user_id)

    async def test_update_place(self, db: AsyncSession):
        user_id = uuid4()

        place_data = {
            "name": "Озеро Рыбное",
            "description": "Красивое озеро в лесу",
            "latitude": 55.75,
            "longitude": 37.61,
            "address": "г. Москва, Example",
            "place_type": "wild",
            "access_type": "car",
            "fish_types": [str(uuid4()), str(uuid4())],
            "seasonality": ["summer", "autumn"],
            "visibility": "private",
            "images": [],
        }

        place = Place(owner_id=user_id, **place_data)
        db.add(place)
        await db.commit()
        await db.refresh(place)

        updated_data = {
            "name": "Озеро Рыбное (обновленное)",
            "description": "Красивое озеро в лесу (обновленное)",
            "visibility": "public",
        }

        from app.crud.place import crud_place as crud

        result = await crud.update(
            db=db, place_id=place.id, place_in=updated_data, user_id=user_id
        )

        assert result is not None
        assert result.visibility == "public"

    async def test_delete_place(self, db: AsyncSession):
        user_id = uuid4()

        place_data = {
            "name": "Озеро Рыбное",
            "description": "Красивое озеро в лесу",
            "latitude": 55.75,
            "longitude": 37.61,
            "address": "г. Москва, Example",
            "place_type": "wild",
            "access_type": "car",
            "fish_types": [str(uuid4()), str(uuid4())],
            "seasonality": ["summer", "autumn"],
            "visibility": "private",
            "images": [],
        }

        place = Place(owner_id=user_id, **place_data)
        db.add(place)
        await db.commit()
        place_id = place.id

        from app.crud.place import crud_place as crud

        result = await crud.delete(db=db, place_id=place_id, user_id=user_id)

        assert result is True

        result = await db.get(Place, place_id)
        assert result is None

    async def test_get_places_with_filters(self, db: AsyncSession):
        user_id = uuid4()

        private_place = Place(
            owner_id=user_id,
            name="Личное место",
            latitude=55.75,
            longitude=37.61,
            address="г. Москва, Example",
            place_type="wild",
            access_type="car",
            fish_types=[str(uuid4())],
            seasonality=["summer"],
            visibility="private",
            images=[],
        )

        public_place = Place(
            owner_id=user_id,
            name="Публичное место",
            latitude=55.75,
            longitude=37.61,
            address="г. Москва, Example",
            place_type="wild",
            access_type="car",
            fish_types=[str(uuid4())],
            seasonality=["summer"],
            visibility="public",
            images=[],
        )

        db.add(private_place)
        db.add(public_place)
        await db.commit()

        from app.crud.place import crud_place as crud

        # Test filter by visibility
        results_private = await crud.get_by_user(
            db=db, user_id=user_id, visibility="private"
        )

        assert results_private.total == 1
        assert len(results_private.places) == 1
        assert results_private.places[0].visibility == "private"

        # Test filter by place_type
        results_wild = await crud.get_by_user(db=db, user_id=user_id, place_type="wild")

        assert results_wild.total == 2
        assert len(results_wild.places) == 2
        assert all(p.place_type == "wild" for p in results_wild.places)

        # Test search by name
        results_search = await crud.get_by_user(
            db=db, user_id=user_id, search="Личное место"
        )

        assert results_search.total == 1
        assert len(results_search.places) == 1
        assert "личное место" in results_search.places[0].name

    async def test_place_validation(self, db: AsyncSession):
        user_id = uuid4()
        # Test empty name
        with pytest.raises(ValueError):
            Place(
                owner_id=user_id,
                name="",
                latitude=55.75,
                longitude=37.61,
                address="г. Москва, Example",
                place_type="wild",
                access_type="car",
                fish_types=[],
                seasonality=[],
                visibility="private",
                images=[],
            )

        # Test invalid place_type
        with pytest.raises(ValueError):
            Place(
                owner_id=user_id,
                name="Test Place",
                latitude=55.75,
                longitude=37.61,
                address="г. Москва, Example",
                place_type="invalid",
                access_type="car",
                fish_types=[],
                seasonality=[],
                visibility="private",
                images=[],
            )

        # Test invalid access_type
        with pytest.raises(ValueError):
            Place(
                owner_id=user_id,
                name="Test Place",
                latitude=55.75,
                longitude=37.61,
                address="g. Москва, Example",
                place_type="wild",
                access_type="invalid",
                fish_types=[],
                seasonality=[],
                visibility="private",
                images=[],
            )

        # Test invalid visibility
        with pytest.raises(ValueError):
            Place(
                owner_id=user_id,
                name="Test Place",
                latitude=55.75,
                longitude=37.61,
                address="g. Москва, Example",
                place_type="wild",
                access_type="car",
                fish_types=[],
                seasonality=[],
                visibility="invalid",
                images=[],
            )

        # Test empty fish_types
        with pytest.raises(ValueError):
            Place(
                owner_id=user_id,
                name="Test Place",
                latitude=55.75,
                longitude=37.61,
                address="g. Москва, Example",
                place_type="wild",
                access_type="car",
                fish_types=[],
                seasonality=[],
                visibility="private",
                images=[],
            )

        # Test invalid seasonality
        with pytest.raises(ValueError):
            Place(
                owner_id=user_id,
                name="Test Place",
                latitude=55.75,
                longitude=37.61,
                address="g. Москва, Example",
                place_type="wild",
                access_type="car",
                fish_types=[str(uuid4())],
                seasonality=["invalid"],
                visibility="private",
                images=[],
            )

        # Test empty images
        with pytest.raises(ValueError):
            Place(
                owner_id=user_id,
                name="Test Place",
                latitude=55.75,
                longitude=37.61,
                address="g. Москва, Example",
                place_type="wild",
                access_type="car",
                fish_types=[str(uuid4())],
                seasonality=[],
                visibility="private",
                images=[],
            )

        # Test too many images
        with pytest.raises(ValueError):
            Place(
                owner_id=user_id,
                name="Test Place",
                latitude=55.75,
                longitude=37.61,
                address="g. Москва, Example",
                place_type="wild",
                access_type="car",
                fish_types=[str(uuid4())],
                seasonality=[],
                visibility="private",
                images=[
                    "http://example.com/photo1.jpg",
                    "http://example.com/photo2.jpg",
                    "http://example.com/photo3.jpg",
                    "http://example.com/photo4.jpg",
                    "http://example.com/photo5.jpg",
                ],
            )

    async def test_place_with_water_type(self, db: AsyncSession):
        user_id = uuid4()

        place_data = {
            "name": "Озеро Рыбное",
            "description": "Красивое озеро в лесу",
            "latitude": 55.75,
            "longitude": 37.61,
            "address": "г. Москва, Example",
            "place_type": "wild",
            "access_type": "car",
            "water_type": "lake",
            "fish_types": [str(uuid4()), str(uuid4())],
            "seasonality": ["summer", "autumn"],
            "visibility": "private",
            "images": [],
        }

        place = Place(owner_id=user_id, **place_data)
        db.add(place)
        await db.commit()
        await db.refresh(place)

        assert place.id is not None
        assert place.water_type == "lake"

    async def test_place_without_photos(self, db: AsyncSession):
        user_id = uuid4()

        place_data = {
            "name": "Дикое место",
            "description": "Место без фото",
            "latitude": 55.75,
            "longitude": 37.61,
            "address": "г. Москва, Example",
            "place_type": "wild",
            "access_type": "car",
            "water_type": "river",
            "fish_types": [str(uuid4())],
            "seasonality": ["summer"],
            "visibility": "private",
            "images": [],
        }

        place = Place(owner_id=user_id, **place_data)
        db.add(place)
        await db.commit()
        await db.refresh(place)

        assert place.id is not None
        assert place.images == []
        assert place.water_type == "river"


@pytest.mark.asyncio
class TestPlaceSchemas:
    async def test_water_type_validation_valid(self):
        from app.schemas.place import PlaceBase

        valid_place = PlaceBase(
            name="Test Place",
            latitude=55.75,
            longitude=37.61,
            address="Test Address",
            place_type="wild",
            access_type="car",
            water_type="lake",
            fish_types=[uuid4()],
        )
        assert valid_place.water_type == "lake"

    async def test_water_type_validation_river(self):
        from app.schemas.place import PlaceBase

        valid_place = PlaceBase(
            name="Test Place",
            latitude=55.75,
            longitude=37.61,
            address="Test Address",
            place_type="wild",
            access_type="car",
            water_type="river",
            fish_types=[uuid4()],
        )
        assert valid_place.water_type == "river"

    async def test_water_type_validation_sea(self):
        from app.schemas.place import PlaceBase

        valid_place = PlaceBase(
            name="Test Place",
            latitude=55.75,
            longitude=37.61,
            address="Test Address",
            place_type="wild",
            access_type="car",
            water_type="sea",
            fish_types=[uuid4()],
        )
        assert valid_place.water_type == "sea"

    async def test_water_type_validation_invalid(self):
        from app.schemas.place import PlaceBase
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PlaceBase(
                name="Test Place",
                latitude=55.75,
                longitude=37.61,
                address="Test Address",
                place_type="wild",
                access_type="car",
                water_type="pond",
                fish_types=[uuid4()],
            )

    async def test_images_optional(self):
        from app.schemas.place import PlaceBase

        place = PlaceBase(
            name="Test Place",
            latitude=55.75,
            longitude=37.61,
            address="Test Address",
            place_type="wild",
            access_type="car",
            water_type="lake",
            fish_types=[uuid4()],
        )
        assert place.images == []

    async def test_water_type_default(self):
        from app.schemas.place import PlaceBase

        place = PlaceBase(
            name="Test Place",
            latitude=55.75,
            longitude=37.61,
            address="Test Address",
            place_type="wild",
            access_type="car",
            fish_types=[uuid4()],
        )
        assert place.water_type == "lake"

    async def test_place_update_water_type(self):
        from app.schemas.place import PlaceUpdate

        update = PlaceUpdate(water_type="river")
        assert update.water_type == "river"

    async def test_place_update_water_type_invalid(self):
        from app.schemas.place import PlaceUpdate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PlaceUpdate(water_type="pond")


@pytest.mark.asyncio
class TestPlaceFishTypesValidation:
    async def test_validate_fish_types_success(self, db: AsyncSession):
        fish_type = FishType(
            name="Щука",
            icon="🐟",
            category="predatory",
            is_active=True,
        )
        db.add(fish_type)
        await db.commit()
        await db.refresh(fish_type)

        from app.crud.place import crud_place

        await crud_place._validate_fish_types(db, [fish_type.id])

    async def test_validate_fish_types_multiple_success(self, db: AsyncSession):
        fish_type1 = FishType(
            name="Щука",
            icon="🐟",
            category="predatory",
            is_active=True,
        )
        fish_type2 = FishType(
            name="Судак",
            icon="🐟",
            category="predatory",
            is_active=True,
        )
        db.add(fish_type1)
        db.add(fish_type2)
        await db.commit()
        await db.refresh(fish_type1)
        await db.refresh(fish_type2)

        from app.crud.place import crud_place

        await crud_place._validate_fish_types(db, [fish_type1.id, fish_type2.id])

    async def test_validate_fish_types_not_found(self, db: AsyncSession):
        non_existent_id = uuid4()

        from app.crud.place import crud_place

        with pytest.raises(ValueError) as exc_info:
            await crud_place._validate_fish_types(db, [non_existent_id])

        assert f"Fish type with id {non_existent_id} not found" in str(exc_info.value)

    async def test_validate_fish_types_partial_not_found(self, db: AsyncSession):
        fish_type = FishType(
            name="Карась",
            icon="🐠",
            category="peaceful",
            is_active=True,
        )
        db.add(fish_type)
        await db.commit()
        await db.refresh(fish_type)

        non_existent_id = uuid4()

        from app.crud.place import crud_place

        with pytest.raises(ValueError) as exc_info:
            await crud_place._validate_fish_types(db, [fish_type.id, non_existent_id])

        assert f"Fish type with id {non_existent_id} not found" in str(exc_info.value)

    async def test_create_place_with_valid_fish_types(self, db: AsyncSession):
        user_id = uuid4()

        fish_type = FishType(
            name="Окунь",
            icon="🐟",
            category="predatory",
            is_active=True,
        )
        db.add(fish_type)
        await db.commit()
        await db.refresh(fish_type)

        from app.crud.place import crud_place
        from app.schemas.place import PlaceCreate

        place_in = PlaceCreate(
            name="Озеро Рыбное",
            description="Тестовое описание",
            latitude=55.75,
            longitude=37.61,
            address="г. Москва, Example",
            place_type="wild",
            access_type="car",
            water_type="lake",
            fish_types=[fish_type.id],
            seasonality=["summer"],
            visibility="private",
            images=[],
        )

        place = await crud_place.create(db=db, place_in=place_in, user_id=user_id)

        assert place.id is not None
        assert place.name == "Озеро Рыбное"
        assert str(fish_type.id) in place.fish_types

    async def test_create_place_with_invalid_fish_types(self, db: AsyncSession):
        user_id = uuid4()
        non_existent_id = uuid4()

        from app.crud.place import crud_place
        from app.schemas.place import PlaceCreate

        place_in = PlaceCreate(
            name="Озеро Рыбное",
            description="Тестовое описание",
            latitude=55.75,
            longitude=37.61,
            address="г. Москва, Example",
            place_type="wild",
            access_type="car",
            water_type="lake",
            fish_types=[non_existent_id],
            seasonality=["summer"],
            visibility="private",
            images=[],
        )

        with pytest.raises(ValueError) as exc_info:
            await crud_place.create(db=db, place_in=place_in, user_id=user_id)

        assert f"Fish type with id {non_existent_id} not found" in str(exc_info.value)

    async def test_create_place_with_empty_fish_types(self, db: AsyncSession):
        user_id = uuid4()

        from app.crud.place import crud_place
        from app.schemas.place import PlaceCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PlaceCreate(
                name="Озеро Рыбное",
                description="Тестовое описание",
                latitude=55.75,
                longitude=37.61,
                address="г. Москва, Example",
                place_type="wild",
                access_type="car",
                water_type="lake",
                fish_types=[],
                seasonality=["summer"],
                visibility="private",
                images=[],
            )
