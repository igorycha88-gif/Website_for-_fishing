import asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, database
from app.models.fish_type import FishType
from app.models.equipment_type import EquipmentType
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def seed_fish_types(db: AsyncSession):
    logger.info("Seeding fish types", service="places-service")

    fish_types_data = [
        {"name": "Щука", "icon": "🐟", "category": "predatory"},
        {"name": "Судак", "icon": "🐟", "category": "predatory"},
        {"name": "Окунь", "icon": "🐟", "category": "predatory"},
        {"name": "Жерех", "icon": "🐟", "category": "predatory"},
        {"name": "Налим", "icon": "🐟", "category": "predatory"},
        {"name": "Голавль", "icon": "🐟", "category": "predatory"},
        {"name": "Карп", "icon": "🐠", "category": "peaceful"},
        {"name": "Лещ", "icon": "🐠", "category": "peaceful"},
        {"name": "Карась", "icon": "🐠", "category": "peaceful"},
        {"name": "Плотва", "icon": "🐠", "category": "peaceful"},
        {"name": "Язь", "icon": "🐠", "category": "peaceful"},
        {"name": "Сазан", "icon": "🐠", "category": "peaceful"},
        {"name": "Амур", "icon": "🐠", "category": "peaceful"},
        {"name": "Линь", "icon": "🐠", "category": "peaceful"},
        {"name": "Густера", "icon": "🐠", "category": "peaceful"},
        {"name": "Красноперка", "icon": "🐠", "category": "peaceful"},
        {"name": "Форель речная", "icon": "🐟", "category": "sport"},
        {"name": "Форель озерная", "icon": "🐟", "category": "sport"},
        {"name": "Лосось", "icon": "🐟", "category": "sport"},
        {"name": "Таймень", "icon": "🐟", "category": "sport"},
        {"name": "Хариус", "icon": "🐟", "category": "sport"},
        {"name": "Сом", "icon": "🐟", "category": "commercial"},
        {"name": "Угорь", "icon": "🐟", "category": "commercial"},
        {"name": "Стерлядь", "icon": "🐟", "category": "commercial"},
        {"name": "Белуга", "icon": "🐟", "category": "commercial"},
        {"name": "Осетр", "icon": "🐟", "category": "commercial"},
    ]

    try:
        for fish_type_data in fish_types_data:
            result = await db.execute(
                select(FishType).where(FishType.name == fish_type_data["name"])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                db_fish_type = FishType(**fish_type_data)
                db.add(db_fish_type)
                logger.info(
                    f"Created fish type: {fish_type_data['name']}",
                    service="places-service",
                )

        await db.commit()
        logger.info("Fish types seeded successfully", service="places-service")

    except Exception as e:
        logger.error(
            "Error seeding fish types",
            service="places-service",
            error=str(e),
            exc_info=True,
        )
        await db.rollback()
        raise


async def seed_equipment_types(db: AsyncSession):
    logger.info("Seeding equipment types", service="places-service")

    equipment_types_data = [
        {"name": "Спиннинг", "category": "rod"},
        {"name": "Фидер", "category": "rod"},
        {"name": "Поплавочная", "category": "rod"},
        {"name": "Карповая", "category": "rod"},
        {"name": "Нахлыст", "category": "rod"},
        {"name": "Кастинговая", "category": "rod"},
        {"name": "Маховая", "category": "rod"},
        {"name": "Безынерционная", "category": "reel"},
        {"name": "Мультипликаторная", "category": "reel"},
        {"name": "Карповая", "category": "reel"},
        {"name": "Фидерная", "category": "reel"},
        {"name": "Воблеры", "category": "bait"},
        {"name": "Блесны", "category": "bait"},
        {"name": "Силикон", "category": "bait"},
        {"name": "Поплавки", "category": "bait"},
        {"name": "Наживка", "category": "bait"},
        {"name": "Насадки", "category": "bait"},
        {"name": "Прикормка", "category": "bait"},
        {"name": "Подсачек", "category": "accessories"},
        {"name": "Садки", "category": "accessories"},
        {"name": "Зевники", "category": "accessories"},
        {"name": "Липгрип", "category": "accessories"},
        {"name": "Кукан", "category": "accessories"},
        {"name": "Кормушки", "category": "accessories"},
    ]

    try:
        for equipment_type_data in equipment_types_data:
            result = await db.execute(
                select(EquipmentType).where(
                    EquipmentType.name == equipment_type_data["name"]
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                db_equipment_type = EquipmentType(**equipment_type_data)
                db.add(db_equipment_type)
                logger.info(
                    f"Created equipment type: {equipment_type_data['name']}",
                    service="places-service",
                )

        await db.commit()
        logger.info("Equipment types seeded successfully", service="places-service")

    except Exception as e:
        logger.error(
            "Error seeding equipment types",
            service="places-service",
            error=str(e),
            exc_info=True,
        )
        await db.rollback()
        raise


async def seed_public_places(db: AsyncSession):
    logger.info("Seeding public places for testing", service="places-service")

    from app.models.place import Place
    from app.models.fish_type import FishType
    from uuid import uuid4

    test_places_data = [
        {
            "name": "Озеро Сенеж",
            "description": "Живописное озеро в Московской области",
            "latitude": 56.0123,
            "longitude": 37.8456,
            "address": "Московская область, Солнечногорский район",
            "place_type": "wild",
            "access_type": "car",
            "water_type": "lake",
            "visibility": "public",
            "is_active": True,
            "seasonality": ["summer", "autumn"],
            "images": [],
        },
        {
            "name": "Река Клязьма",
            "description": "Участок реки Клязьма с хорошей популяцией жереха и голавля",
            "latitude": 55.6789,
            "longitude": 38.1234,
            "address": "Московская область, Клязьминский район",
            "place_type": "wild",
            "access_type": "car",
            "water_type": "river",
            "visibility": "public",
            "is_active": True,
            "seasonality": ["spring", "summer", "autumn"],
            "images": [],
        },
        {
            "name": "Рыболовная база Истра",
            "description": "Комфортная база отдыха с прокатом катеров и арендой снастей",
            "latitude": 55.9123,
            "longitude": 37.0456,
            "address": "Московская область, г. Истра, ул. Рыбацкая 15",
            "place_type": "resort",
            "access_type": "car",
            "water_type": "lake",
            "visibility": "public",
            "is_active": True,
            "seasonality": ["spring", "summer", "autumn", "winter"],
            "images": [],
        },
        {
            "name": "Кэмпинг на Пироговском водохранилище",
            "description": "Дикий кэмпинг на берегу",
            "latitude": 56.5432,
            "longitude": 37.8234,
            "address": "Московская область",
            "place_type": "camping",
            "access_type": "car",
            "water_type": "reservoir",
            "visibility": "public",
            "is_active": True,
            "seasonality": ["summer"],
            "images": [],
        },
    ]

    try:
        result = await db.execute(select(FishType).limit(5))
        fish_types = result.scalars().all()
        fish_type_ids = [ft.id for ft in fish_types[:3]]

        for place_data in test_places_data:
            result = await db.execute(
                select(Place).where(Place.name == place_data["name"])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                db_place = Place(
                    owner_id=uuid4(), fish_types=fish_type_ids[:2], **place_data
                )
                db.add(db_place)
                logger.info(
                    f"Created public place: {place_data['name']}",
                    service="places-service",
                )

        await db.commit()
        logger.info("Public places seeded successfully", service="places-service")

    except Exception as e:
        logger.error(
            "Error seeding public places",
            service="places-service",
            error=str(e),
            exc_info=True,
        )
        await db.rollback()
        raise


async def seed_all():
    async for db in get_db():
        await seed_fish_types(db)
        await seed_equipment_types(db)
        # await seed_public_places(db)  # Disabled - requires existing user
        logger.info("All seed data created successfully", service="places-service")


if __name__ == "__main__":
    asyncio.run(seed_all())
