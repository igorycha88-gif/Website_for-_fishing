import asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
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


async def seed_catch_points(db: AsyncSession):
    logger.info("Seeding catch points (Volga/Oka)", service="places-service")

    from app.models.catch_point import CatchPoint
    from sqlalchemy import select as _select

    catches_data = [
        # ===== ВОЛГА (volga) =====
        # Тверь / Верхняя Волга
        {"river": "volga", "name": "Верхняя Волга — Тверь", "lat": 56.8600, "lon": 35.9200,
         "fish": "Щука", "season": ["summer", "autumn"], "depth": 3.5, "bait": "Воблер, блесна", "weight": 2.1,
         "desc": "Закоряженные ямы ниже Твери, стабильный клёв щуки по открытой воде."},
        {"river": "volga", "name": "Верхняя Волга — Тверь", "lat": 56.8750, "lon": 35.9900,
         "fish": "Окунь", "season": ["summer", "autumn", "winter"], "depth": 4.0, "bait": "Мормышка, балансир", "weight": 0.4,
         "desc": "Окуневые котлы в конце лета."},
        {"river": "volga", "name": "Иваньковское вдхр — Конаково", "lat": 56.8500, "lon": 36.8000,
         "fish": "Судак", "season": ["summer", "autumn"], "depth": 7.0, "bait": "Джиг, силикон", "weight": 1.8,
         "desc": "Русло, бровки, ночной судак."},
        {"river": "volga", "name": "Иваньковское вдхр — Конаково", "lat": 56.8320, "lon": 36.8600,
         "fish": "Лещ", "season": ["spring", "summer"], "depth": 6.0, "bait": "Фидер, опарыш", "weight": 1.2,
         "desc": "Стайный лещ на фидер на русловых бровках."},
        # Угличское / Калязин
        {"river": "volga", "name": "Угличское вдхр — Калязин", "lat": 57.1800, "lon": 37.8500,
         "fish": "Жерех", "season": ["summer"], "depth": 2.5, "bait": "Кастмастер, девон", "weight": 2.5,
         "desc": "Жереховые котлы на перекатах в июле-августе."},
        {"river": "volga", "name": "Угличское вдхр — Калязин", "lat": 57.2100, "lon": 37.9100,
         "fish": "Щука", "season": ["spring", "autumn"], "depth": 3.0, "bait": "Воблер, поппер", "weight": 3.0,
         "desc": "Заливные луга, мелководье."},
        {"river": "volga", "name": "Угличское вдхр — Калязин", "lat": 57.1600, "lon": 37.7800,
         "fish": "Плотва", "season": ["spring", "summer"], "depth": 2.0, "bait": "Поплавок, перловка", "weight": 0.25,
         "desc": "Весенняя плотва на прогреве."},
        # Рыбинское вдхр
        {"river": "volga", "name": "Рыбинское вдхр — Молога", "lat": 58.0500, "lon": 38.8500,
         "fish": "Судак", "season": ["summer", "autumn"], "depth": 8.0, "bait": "Джиг, поролонка", "weight": 2.2,
         "desc": "Глубокие ямы, судак на русле Мологи."},
        {"river": "volga", "name": "Рыбинское вдхр — Молога", "lat": 58.0200, "lon": 38.7900,
         "fish": "Окунь", "season": ["summer", "autumn", "winter"], "depth": 5.0, "bait": "Блесна, балансир", "weight": 0.6,
         "desc": "Крупный горбач на камнях."},
        {"river": "volga", "name": "Рыбинское вдхр — Молога", "lat": 58.0700, "lon": 38.9100,
         "fish": "Налим", "season": ["autumn", "winter"], "depth": 9.0, "bait": "Донка, ерш", "weight": 1.1,
         "desc": "Ночной налим в холодной воде."},
        # Ярославль
        {"river": "volga", "name": "Волга — Ярославль", "lat": 57.6300, "lon": 39.8700,
         "fish": "Лещ", "season": ["spring", "summer", "autumn"], "depth": 6.5, "bait": "Фидер, горох", "weight": 1.5,
         "desc": "Яровая бровка, стайный лещ."},
        {"river": "volga", "name": "Волга — Ярославль", "lat": 57.6500, "lon": 39.9300,
         "fish": "Щука", "season": ["summer", "autumn"], "depth": 3.5, "bait": "Воблер, колебалка", "weight": 2.8,
         "desc": "Травянистые банки ниже города."},
        {"river": "volga", "name": "Волга — Ярославль", "lat": 57.6100, "lon": 39.8200,
         "fish": "Голавль", "season": ["summer"], "depth": 1.8, "bait": "Воблер-крэнк, кузнечик", "weight": 0.9,
         "desc": "Перекаты, голавль на перекатах."},
        # Кострома
        {"river": "volga", "name": "Волга — Кострома", "lat": 57.7700, "lon": 40.9300,
         "fish": "Судак", "season": ["summer", "autumn"], "depth": 7.5, "bait": "Джиг", "weight": 2.0,
         "desc": "Судачьи ямы ниже Костромы."},
        {"river": "volga", "name": "Волга — Кострома", "lat": 57.7900, "lon": 40.9900,
         "fish": "Жерех", "season": ["summer"], "depth": 2.8, "bait": "Пилястровый воблер", "weight": 2.3,
         "desc": "Жерех на сужениях русла."},
        {"river": "volga", "name": "Волга — Кострома", "lat": 57.7500, "lon": 40.8700,
         "fish": "Язь", "season": ["spring", "summer"], "depth": 2.5, "bait": "Воблер, червь", "weight": 1.0,
         "desc": "Язь на границе течения."},
        # Горьковское вдхр
        {"river": "volga", "name": "Горьковское вдхр — Городец", "lat": 56.6500, "lon": 43.4700,
         "fish": "Лещ", "season": ["spring", "summer", "autumn"], "depth": 8.0, "bait": "Фидер", "weight": 1.6,
         "desc": "Глубокий лещ на фидер."},
        {"river": "volga", "name": "Горьковское вдхр — Городец", "lat": 56.6700, "lon": 43.5200,
         "fish": "Окунь", "season": ["summer", "autumn", "winter"], "depth": 4.5, "bait": "Балансир, мормышка", "weight": 0.5,
         "desc": "Окунь на банках."},
        {"river": "volga", "name": "Горьковское вдхр — Городец", "lat": 56.6300, "lon": 43.4200,
         "fish": "Щука", "season": ["spring", "autumn"], "depth": 3.0, "bait": "Воблер, джерк", "weight": 3.5,
         "desc": "Трава и коряги."},
        # Чебоксарское вдхр
        {"river": "volga", "name": "Чебоксарское вдхр — Козьмодемьянск", "lat": 56.3300, "lon": 46.5700,
         "fish": "Судак", "season": ["summer", "autumn"], "depth": 9.0, "bait": "Джиг, твичинг", "weight": 2.4,
         "desc": "Судак на русловых бровках."},
        {"river": "volga", "name": "Чебоксарское вдхр — Козьмодемьянск", "lat": 56.3000, "lon": 46.5200,
         "fish": "Жерех", "season": ["summer"], "depth": 3.0, "bait": "Кастмастер", "weight": 2.7,
         "desc": "Жерех в верхних слоях."},
        {"river": "volga", "name": "Чебоксарское вдхр — Козьмодемьянск", "lat": 56.3500, "lon": 46.6200,
         "fish": "Сом", "season": ["summer"], "depth": 12.0, "bait": "Квок, живец", "weight": 8.0,
         "desc": "Сом на ямах, ловля на квок."},
        # Казань / Куйбышевское
        {"river": "volga", "name": "Куйбышевское вдхр — Казань", "lat": 55.7900, "lon": 49.1200,
         "fish": "Лещ", "season": ["spring", "summer"], "depth": 9.0, "bait": "Фидер, опарыш", "weight": 1.4,
         "desc": "Стайный лещ на широких плёсах."},
        {"river": "volga", "name": "Куйбышевское вдхр — Казань", "lat": 55.7700, "lon": 49.0800,
         "fish": "Сазан", "season": ["summer"], "depth": 5.0, "bait": "Бойл, кукуруза", "weight": 5.5,
         "desc": "Дикий сазан на бойлы."},
        {"river": "volga", "name": "Куйбышевское вдхр — Казань", "lat": 55.8100, "lon": 49.1600,
         "fish": "Щука", "season": ["autumn"], "depth": 4.0, "bait": "Воблер", "weight": 4.0,
         "desc": "Осенняя трофейная щука."},

        # ===== ОКА (oka) =====
        # Калуга
        {"river": "oka", "name": "Ока — Калуга", "lat": 54.5100, "lon": 36.2600,
         "fish": "Голавль", "season": ["summer"], "depth": 2.0, "bait": "Воблер-крэнк", "weight": 1.2,
         "desc": "Голавль на перекатах под Калугой."},
        {"river": "oka", "name": "Ока — Калуга", "lat": 54.5300, "lon": 36.3100,
         "fish": "Щука", "season": ["spring", "autumn"], "depth": 2.8, "bait": "Воблер, блесна", "weight": 2.4,
         "desc": "Щука в заливах и старицах."},
        {"river": "oka", "name": "Ока — Калуга", "lat": 54.4900, "lon": 36.2200,
         "fish": "Плотва", "season": ["spring", "summer"], "depth": 1.8, "bait": "Поплавок", "weight": 0.3,
         "desc": "Весенняя плотва на прогреве."},
        # Алексин / Серпухов
        {"river": "oka", "name": "Ока — Алексин", "lat": 54.5000, "lon": 37.0700,
         "fish": "Жерех", "season": ["summer"], "depth": 2.5, "bait": "Девон, кастмастер", "weight": 2.0,
         "desc": "Жерех на быстрине."},
        {"river": "oka", "name": "Ока — Серпухов", "lat": 54.9200, "lon": 37.4000,
         "fish": "Судак", "season": ["summer", "autumn"], "depth": 6.0, "bait": "Джиг", "weight": 1.9,
         "desc": "Судак на ямах ниже Серпухова."},
        {"river": "oka", "name": "Ока — Серпухов", "lat": 54.9000, "lon": 37.3600,
         "fish": "Язь", "season": ["spring", "summer"], "depth": 2.5, "bait": "Воблер", "weight": 1.1,
         "desc": "Язь на свалах."},
        {"river": "oka", "name": "Ока — Серпухов", "lat": 54.9400, "lon": 37.4400,
         "fish": "Лещ", "season": ["summer"], "depth": 5.0, "bait": "Фидер", "weight": 1.3,
         "desc": "Лещ на русловых бровках."},
        # Коломна
        {"river": "oka", "name": "Ока — Коломна", "lat": 55.0900, "lon": 38.7800,
         "fish": "Щука", "season": ["spring", "autumn"], "depth": 3.0, "bait": "Воблер", "weight": 2.6,
         "desc": "Щука в районе устья Москвы-реки."},
        {"river": "oka", "name": "Ока — Коломна", "lat": 55.1100, "lon": 38.8200,
         "fish": "Окунь", "season": ["summer", "autumn"], "depth": 3.5, "bait": "Блесна", "weight": 0.45,
         "desc": "Окунь на песчаных косах."},
        {"river": "oka", "name": "Ока — Коломна", "lat": 55.0700, "lon": 38.7500,
         "fish": "Голавль", "season": ["summer"], "depth": 2.0, "bait": "Крэнк", "weight": 1.0,
         "desc": "Голавль на перекатах."},
        # Рязань
        {"river": "oka", "name": "Ока — Рязань", "lat": 54.6300, "lon": 39.7400,
         "fish": "Лещ", "season": ["spring", "summer", "autumn"], "depth": 5.5, "bait": "Фидер, горох", "weight": 1.5,
         "desc": "Лещ на фидер ниже Рязани."},
        {"river": "oka", "name": "Ока — Рязань", "lat": 54.6500, "lon": 39.7900,
         "fish": "Судак", "season": ["summer", "autumn"], "depth": 6.5, "bait": "Джиг", "weight": 2.1,
         "desc": "Судак на русловых ямах."},
        {"river": "oka", "name": "Ока — Рязань", "lat": 54.6100, "lon": 39.7000,
         "fish": "Жерех", "season": ["summer"], "depth": 2.8, "bait": "Кастмастер", "weight": 2.2,
         "desc": "Жереховые котлы."},
        # Касимов
        {"river": "oka", "name": "Ока — Касимов", "lat": 54.9400, "lon": 41.3900,
         "fish": "Щука", "season": ["autumn"], "depth": 3.2, "bait": "Воблер, джерк", "weight": 3.2,
         "desc": "Осенняя щука на раскатах."},
        {"river": "oka", "name": "Ока — Касимов", "lat": 54.9200, "lon": 41.3500,
         "fish": "Налим", "season": ["autumn", "winter"], "depth": 6.0, "bait": "Донка, живец", "weight": 1.0,
         "desc": "Ночной налим."},
        # Муром
        {"river": "oka", "name": "Ока — Муром", "lat": 55.5700, "lon": 42.0500,
         "fish": "Лещ", "season": ["summer"], "depth": 5.0, "bait": "Фидер", "weight": 1.4,
         "desc": "Стайный лещ."},
        {"river": "oka", "name": "Ока — Муром", "lat": 55.5900, "lon": 42.1000,
         "fish": "Судак", "season": ["summer", "autumn"], "depth": 6.5, "bait": "Джиг", "weight": 2.0,
         "desc": "Судак на бровках."},
        {"river": "oka", "name": "Ока — Муром", "lat": 55.5500, "lon": 42.0100,
         "fish": "Голавль", "season": ["summer"], "depth": 2.0, "bait": "Воблер", "weight": 1.1,
         "desc": "Голавль на струе."},
        # Павлово / низовья Оки
        {"river": "oka", "name": "Ока — Павлово", "lat": 55.9700, "lon": 42.9900,
         "fish": "Жерех", "season": ["summer"], "depth": 3.0, "bait": "Пилястер, девон", "weight": 2.4,
         "desc": "Жерех в низовьях Оки."},
        {"river": "oka", "name": "Ока — Павлово", "lat": 55.9500, "lon": 42.9500,
         "fish": "Щука", "season": ["spring", "autumn"], "depth": 3.0, "bait": "Воблер", "weight": 2.9,
         "desc": "Щука в заливах."},
        {"river": "oka", "name": "Ока — устье (слияние с Волгой)", "lat": 56.3200, "lon": 43.9500,
         "fish": "Сом", "season": ["summer"], "depth": 10.0, "bait": "Квок, живец", "weight": 9.5,
         "desc": "Сом на ямах в районе слияния с Волгой."},
        {"river": "oka", "name": "Ока — устье (слияние с Волгой)", "lat": 56.3000, "lon": 43.9200,
         "fish": "Судак", "season": ["summer", "autumn"], "depth": 8.0, "bait": "Джиг", "weight": 2.5,
         "desc": "Судак в устьевой зоне."},
    ]

    try:
        fish_by_name: dict = {}
        result = await db.execute(_select(FishType))
        for ft in result.scalars().all():
            fish_by_name[ft.name] = ft

        created = 0
        for item in catches_data:
            fish = fish_by_name.get(item["fish"])
            if not fish:
                logger.warning(
                    f"Fish type not found, skip: {item['fish']}",
                    service="places-service",
                )
                continue

            existing = await db.execute(
                _select(CatchPoint).where(
                    CatchPoint.latitude == item["lat"],
                    CatchPoint.longitude == item["lon"],
                    CatchPoint.fish_type_id == fish.id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            db.add(
                CatchPoint(
                    latitude=item["lat"],
                    longitude=item["lon"],
                    fish_type_id=fish.id,
                    river=item["river"],
                    name=item["name"],
                    description=item["desc"],
                    season=item["season"],
                    depth=item["depth"],
                    bait=item["bait"],
                    weight_avg=item["weight"],
                    is_demo=True,
                    source_label="Демонстрационные данные",
                    is_active=True,
                )
            )
            created += 1

        await db.commit()
        logger.info(
            "Catch points seeded successfully",
            service="places-service",
            created=created,
        )

    except Exception as e:
        logger.error(
            "Error seeding catch points",
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
        await seed_catch_points(db)
        # await seed_public_places(db)  # Disabled - requires existing user
        logger.info("All seed data created successfully", service="places-service")


if __name__ == "__main__":
    asyncio.run(seed_all())
