import asyncio

from sqlalchemy import text

from app.core.database import async_session, engine
from app.core.logging_config import get_logger

logger = get_logger(__name__)

WATER_BODIES = [
    {
        "name": "Ладожское озеро",
        "water_type": "lake",
        "lat_min": 59.55, "lat_max": 61.80,
        "lon_min": 29.50, "lon_max": 33.50,
        "centroid_lat": 60.67, "centroid_lon": 31.50,
        "max_depth": 230.0, "avg_depth": 51.0,
        "area_km2": 17700.0, "region": "Республика Карелия / Ленинградская область",
    },
    {
        "name": "Онежское озеро",
        "water_type": "lake",
        "lat_min": 60.60, "lat_max": 62.40,
        "lon_min": 33.80, "lon_max": 36.50,
        "centroid_lat": 61.50, "centroid_lon": 35.20,
        "max_depth": 120.0, "avg_depth": 30.0,
        "area_km2": 9700.0, "region": "Республика Карелия",
    },
    {
        "name": "Озеро Байкал",
        "water_type": "lake",
        "lat_min": 51.30, "lat_max": 55.90,
        "lon_min": 103.70, "lon_max": 109.90,
        "centroid_lat": 53.50, "centroid_lon": 108.00,
        "max_depth": 1642.0, "avg_depth": 744.0,
        "area_km2": 31722.0, "region": "Иркутская область / Республика Бурятия",
    },
    {
        "name": "Куйбышевское водохранилище",
        "water_type": "reservoir",
        "lat_min": 54.30, "lat_max": 55.80,
        "lon_min": 48.50, "lon_max": 51.50,
        "centroid_lat": 55.05, "centroid_lon": 50.00,
        "max_depth": 41.0, "avg_depth": 10.0,
        "area_km2": 6450.0, "region": "Республика Татарстан / Самарская область",
    },
    {
        "name": "Рыбинское водохранилище",
        "water_type": "reservoir",
        "lat_min": 57.80, "lat_max": 58.90,
        "lon_min": 37.40, "lon_max": 39.80,
        "centroid_lat": 58.35, "centroid_lon": 38.60,
        "max_depth": 30.0, "avg_depth": 5.2,
        "area_km2": 4580.0, "region": "Ярославская область",
    },
    {
        "name": "Цимлянское водохранилище",
        "water_type": "reservoir",
        "lat_min": 47.20, "lat_max": 49.20,
        "lon_min": 42.00, "lon_max": 44.50,
        "centroid_lat": 48.20, "centroid_lon": 43.20,
        "max_depth": 36.0, "avg_depth": 8.8,
        "area_km2": 2700.0, "region": "Ростовская область / Волгоградская область",
    },
    {
        "name": "Озеро Селигер",
        "water_type": "lake",
        "lat_min": 56.90, "lat_max": 57.35,
        "lon_min": 32.50, "lon_max": 33.30,
        "centroid_lat": 57.17, "centroid_lon": 32.95,
        "max_depth": 24.0, "avg_depth": 5.2,
        "area_km2": 260.0, "region": "Тверская область",
    },
    {
        "name": "Озеро Ильмень",
        "water_type": "lake",
        "lat_min": 57.20, "lat_max": 58.10,
        "lon_min": 30.60, "lon_max": 32.20,
        "centroid_lat": 57.65, "centroid_lon": 31.40,
        "max_depth": 10.0, "avg_depth": 4.0,
        "area_km2": 982.0, "region": "Новгородская область",
    },
    {
        "name": "Озеро Плещеево",
        "water_type": "lake",
        "lat_min": 56.76, "lat_max": 56.84,
        "lon_min": 38.76, "lon_max": 38.88,
        "centroid_lat": 56.80, "centroid_lon": 38.82,
        "max_depth": 24.0, "avg_depth": 11.0,
        "area_km2": 51.0, "region": "Ярославская область",
    },
    {
        "name": "Озеро Сенеж",
        "water_type": "lake",
        "lat_min": 56.10, "lat_max": 56.22,
        "lon_min": 36.95, "lon_max": 37.12,
        "centroid_lat": 56.16, "centroid_lon": 37.03,
        "max_depth": 6.0, "avg_depth": 3.5,
        "area_km2": 8.5, "region": "Московская область",
    },
    {
        "name": "Озеро Валдай",
        "water_type": "lake",
        "lat_min": 57.92, "lat_max": 58.02,
        "lon_min": 33.20, "lon_max": 33.36,
        "centroid_lat": 57.97, "centroid_lon": 33.28,
        "max_depth": 60.0, "avg_depth": 17.0,
        "area_km2": 19.7, "region": "Новгородская область",
    },
    {
        "name": "Волгоградское водохранилище",
        "water_type": "reservoir",
        "lat_min": 48.50, "lat_max": 50.50,
        "lon_min": 44.20, "lon_max": 46.50,
        "centroid_lat": 49.50, "centroid_lon": 45.30,
        "max_depth": 41.0, "avg_depth": 10.0,
        "area_km2": 3117.0, "region": "Волгоградская область / Саратовская область",
    },
    {
        "name": "Саратовское водохранилище",
        "water_type": "reservoir",
        "lat_min": 50.50, "lat_max": 52.50,
        "lon_min": 46.50, "lon_max": 49.00,
        "centroid_lat": 51.50, "centroid_lon": 47.70,
        "max_depth": 31.0, "avg_depth": 7.0,
        "area_km2": 1831.0, "region": "Самарская область / Саратовская область",
    },
    {
        "name": "Горьковское водохранилище",
        "water_type": "reservoir",
        "lat_min": 56.10, "lat_max": 57.70,
        "lon_min": 41.00, "lon_max": 44.00,
        "centroid_lat": 57.00, "centroid_lon": 42.80,
        "max_depth": 22.0, "avg_depth": 3.6,
        "area_km2": 1590.0, "region": "Ярославская область / Ивановская область",
    },
    {
        "name": "Чебоксарское водохранилище",
        "water_type": "reservoir",
        "lat_min": 55.40, "lat_max": 56.30,
        "lon_min": 43.80, "lon_max": 46.50,
        "centroid_lat": 55.90, "centroid_lon": 45.30,
        "max_depth": 21.0, "avg_depth": 4.0,
        "area_km2": 1080.0, "region": "Чувашская Республика / Республика Марий Эл",
    },
    {
        "name": "Озеро Лача",
        "water_type": "lake",
        "lat_min": 61.10, "lat_max": 61.40,
        "lon_min": 40.50, "lon_max": 41.20,
        "centroid_lat": 61.25, "centroid_lon": 40.85,
        "max_depth": 6.0, "avg_depth": 1.5,
        "area_km2": 354.0, "region": "Архангельская область",
    },
    {
        "name": "Озеро Кенозеро",
        "water_type": "lake",
        "lat_min": 61.60, "lat_max": 61.90,
        "lon_min": 38.20, "lon_max": 38.70,
        "centroid_lat": 61.75, "centroid_lon": 38.45,
        "max_depth": 90.0, "avg_depth": 8.0,
        "area_km2": 68.6, "region": "Архангельская область",
    },
    {
        "name": "Озеро Топозеро",
        "water_type": "lake",
        "lat_min": 63.60, "lat_max": 64.40,
        "lon_min": 31.50, "lon_max": 33.00,
        "centroid_lat": 64.05, "centroid_lon": 32.30,
        "max_depth": 56.0, "avg_depth": 15.0,
        "area_km2": 986.0, "region": "Республика Карелия",
    },
    {
        "name": "Озеро Пяозеро",
        "water_type": "lake",
        "lat_min": 64.10, "lat_max": 64.50,
        "lon_min": 31.80, "lon_max": 32.70,
        "centroid_lat": 64.30, "centroid_lon": 32.20,
        "max_depth": 49.0, "avg_depth": 15.0,
        "area_km2": 659.0, "region": "Республика Карелия",
    },
    {
        "name": "Озеро Имандра",
        "water_type": "lake",
        "lat_min": 67.30, "lat_max": 68.10,
        "lon_min": 32.50, "lon_max": 33.50,
        "centroid_lat": 67.70, "centroid_lon": 33.00,
        "max_depth": 67.0, "avg_depth": 16.0,
        "area_km2": 876.0, "region": "Мурманская область",
    },
    {
        "name": "Камское водохранилище",
        "water_type": "reservoir",
        "lat_min": 57.50, "lat_max": 59.50,
        "lon_min": 53.50, "lon_max": 56.50,
        "centroid_lat": 58.50, "centroid_lon": 55.00,
        "max_depth": 30.0, "avg_depth": 6.3,
        "area_km2": 1915.0, "region": "Пермский край",
    },
    {
        "name": "Воткинское водохранилище",
        "water_type": "reservoir",
        "lat_min": 56.40, "lat_max": 57.80,
        "lon_min": 53.50, "lon_max": 55.00,
        "centroid_lat": 57.10, "centroid_lon": 54.20,
        "max_depth": 28.0, "avg_depth": 6.5,
        "area_km2": 1120.0, "region": "Пермский край / Удмуртская Республика",
    },
    {
        "name": "Братское водохранилище",
        "water_type": "reservoir",
        "lat_min": 52.80, "lat_max": 56.20,
        "lon_min": 99.00, "lon_max": 104.00,
        "centroid_lat": 54.50, "centroid_lon": 101.50,
        "max_depth": 150.0, "avg_depth": 31.0,
        "area_km2": 5470.0, "region": "Иркутская область",
    },
    {
        "name": "Красноярское водохранилище",
        "water_type": "reservoir",
        "lat_min": 53.50, "lat_max": 56.20,
        "lon_min": 91.00, "lon_max": 93.00,
        "centroid_lat": 55.00, "centroid_lon": 92.00,
        "max_depth": 105.0, "avg_depth": 40.0,
        "area_km2": 2000.0, "region": "Красноярский край",
    },
    {
        "name": "Озеро Ханка",
        "water_type": "lake",
        "lat_min": 44.30, "lat_max": 45.10,
        "lon_min": 131.50, "lon_max": 132.80,
        "centroid_lat": 44.90, "centroid_lon": 132.30,
        "max_depth": 10.6, "avg_depth": 4.5,
        "area_km2": 4070.0, "region": "Приморский край",
    },
    {
        "name": "Озеро Таймыр",
        "water_type": "lake",
        "lat_min": 73.80, "lat_max": 74.80,
        "lon_min": 99.00, "lon_max": 108.00,
        "centroid_lat": 74.30, "centroid_lon": 103.50,
        "max_depth": 26.0, "avg_depth": 2.8,
        "area_km2": 4560.0, "region": "Красноярский край",
    },
    {
        "name": "Озеро Чудско-Псковское",
        "water_type": "lake",
        "lat_min": 57.50, "lat_max": 58.80,
        "lon_min": 26.90, "lon_max": 28.30,
        "centroid_lat": 58.15, "centroid_lon": 27.60,
        "max_depth": 15.0, "avg_depth": 7.1,
        "area_km2": 3558.0, "region": "Псковская область",
    },
    {
        "name": "Водохранилище Иваньковское",
        "water_type": "reservoir",
        "lat_min": 56.40, "lat_max": 57.20,
        "lon_min": 35.40, "lon_max": 36.90,
        "centroid_lat": 56.80, "centroid_lon": 36.20,
        "max_depth": 19.0, "avg_depth": 5.0,
        "area_km2": 327.0, "region": "Тверская область",
    },
    {
        "name": "Угличское водохранилище",
        "water_type": "reservoir",
        "lat_min": 56.50, "lat_max": 57.60,
        "lon_min": 37.20, "lon_max": 38.50,
        "centroid_lat": 57.10, "centroid_lon": 37.90,
        "max_depth": 25.0, "avg_depth": 5.0,
        "area_km2": 249.0, "region": "Тверская область / Ярославская область",
    },
]


async def seed():
    logger.info(
        "seed_start",
        service="depth-service",
        action="seed_water_bodies",
        count=len(WATER_BODIES),
    )

    async with async_session() as session:
        for wb in WATER_BODIES:
            await session.execute(
                text(
                    """
                    INSERT INTO ru_water_bodies
                        (name, water_type, lat_min, lat_max, lon_min, lon_max,
                         centroid_lat, centroid_lon, max_depth, avg_depth,
                         area_km2, region)
                    VALUES
                        (:name, :water_type, :lat_min, :lat_max, :lon_min, :lon_max,
                         :centroid_lat, :centroid_lon, :max_depth, :avg_depth,
                         :area_km2, :region)
                    ON CONFLICT DO NOTHING
                    """
                ),
                wb,
            )
        await session.commit()

    logger.info(
        "seed_completed",
        service="depth-service",
        action="seed_water_bodies",
        inserted=len(WATER_BODIES),
    )
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
