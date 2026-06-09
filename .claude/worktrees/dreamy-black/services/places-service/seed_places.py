#!/usr/bin/env python3
"""
Seed script for places-service
Creates sample fishing places for testing
"""

import asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import DATABASE_URL
from app.models.place import Place

SAMPLE_PLACES = [
    {
        "title": "Озеро Карасево",
        "description": "Прекрасное озеро для ловли карася и леща. Чистая вода, удобный берег. Рекомендую брать фидер и прикормку.",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "address": "Москва, Ленинградский проспект, 1",
        "city": "Москва",
        "region": "Московская область",
        "price_per_day": 500.0,
        "max_people": 5,
        "facilities": ["parking", "toilet"],
        "fish_types": ["carp", "bream", "roach"],
        "images": [],
        "is_public": True,
        "status": "active",
        "rating_avg": 4.5,
        "reviews_count": 12,
    },
    {
        "title": "Река Ока - Ловля щуки",
        "description": "Отличное место для ловли щуки и судака. Глубина до 3 метров. Лучшее время - раннее утро и вечер. Нужна лодка.",
        "latitude": 55.6800,
        "longitude": 37.7300,
        "address": "Московская область, река Ока, возле д. Коломна",
        "city": "Коломна",
        "region": "Московская область",
        "price_per_day": 1000.0,
        "max_people": 3,
        "facilities": ["parking", "boat_rental", "camping"],
        "fish_types": ["pike", "zander", "perch"],
        "images": [],
        "is_public": True,
        "status": "active",
        "rating_avg": 4.8,
        "reviews_count": 25,
    },
    {
        "title": "Старица реки - Ловля форели",
        "description": "Тайное место для ловли форели. Кристально чистая вода, берег заросший. Нужна удочка и нахлыст.",
        "latitude": 55.7200,
        "longitude": 37.6500,
        "address": "Москва, природный парк Царицыно",
        "city": "Москва",
        "region": "Московская область",
        "price_per_day": None,
        "max_people": 2,
        "facilities": ["parking"],
        "fish_types": ["trout", "rainbow_trout"],
        "images": [],
        "is_public": False,
        "status": "active",
        "rating_avg": 5.0,
        "reviews_count": 3,
    },
    {
        "title": "Пруд на даче",
        "description": "Мой личный пруд на даче. Можно ловить карася и плотву. Бесплатно для друзей.",
        "latitude": 55.7900,
        "longitude": 37.5800,
        "address": "Московская область, д. Барвиха",
        "city": "Барвиха",
        "region": "Московская область",
        "price_per_day": 0.0,
        "max_people": 4,
        "facilities": ["parking", "bbq", "camping", "fireplace"],
        "fish_types": ["carp", "roach", "silver_bream"],
        "images": [],
        "is_public": False,
        "status": "active",
        "rating_avg": 4.2,
        "reviews_count": 8,
    },
    {
        "title": "Карьер - Ловля сома",
        "description": "Глубокий карьер с отличной популяцией сома. Нужна мощная снасть и живец. Опасно для детей!",
        "latitude": 55.7100,
        "longitude": 37.8000,
        "address": "Московская область, Балашихинский район",
        "city": "Балашиха",
        "region": "Московская область",
        "price_per_day": 300.0,
        "max_people": 10,
        "facilities": ["parking", "toilet", "shop"],
        "fish_types": ["catfish", "carp", "bream"],
        "images": [],
        "is_public": True,
        "status": "active",
        "rating_avg": 4.0,
        "reviews_count": 15,
    },
]


async def seed_places():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        owner_id = uuid.UUID("cc530cf8-925a-4829-984d-561f3d1c2def")

        for place_data in SAMPLE_PLACES:
            place = Place(
                id=uuid.uuid4(),
                owner_id=owner_id,
                **place_data,
                visit_date=datetime.now() if not place_data.get("is_public") else None,
            )
            session.add(place)
            print(f"Added place: {place_data['title']}")

        await session.commit()
        print(f"\nTotal places seeded: {len(SAMPLE_PLACES)}")


if __name__ == "__main__":
    asyncio.run(seed_places())
