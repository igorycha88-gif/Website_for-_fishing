
from app.core.logging_config import get_logger
from app.core.redis_client import cache_get, cache_set
from app.services import gvr_cache, osm_overpass_client
from app.services.depth_reader import query_depth as query_gebco

logger = get_logger(__name__)


def _cache_key(lat: float, lon: float) -> str:
    return f"depth:{lat:.4f}:{lon:.4f}"


def _no_data(lat: float, lon: float) -> dict:
    return {
        "depth": None,
        "depth_display": None,
        "source": None,
        "accuracy_m": None,
        "has_data": False,
        "lat": lat,
        "lon": lon,
        "water_body_name": None,
        "water_body_type": None,
        "depth_type": None,
    }


async def resolve_depth(lat: float, lon: float) -> dict:
    logger.info(
        "depth_resolver_start",
        service="depth-service",
        action="depth_resolver",
        lat=lat,
        lon=lon,
    )

    key = _cache_key(lat, lon)
    cached = await cache_get(key)
    if cached is not None:
        logger.info(
            "depth_resolver_cache_hit",
            service="depth-service",
            action="depth_resolver",
            lat=lat,
            lon=lon,
            source=cached.get("source"),
        )
        return cached

    osm_result = await osm_overpass_client.query_water_body(lat, lon)

    if osm_result and osm_result.get("has_data"):
        result = _build_result(lat, lon, osm_result)
        await cache_set(key, result)
        logger.info(
            "depth_resolver_osm_hit",
            service="depth-service",
            action="depth_resolver",
            lat=lat,
            lon=lon,
            name=osm_result.get("name"),
        )
        return result

    if osm_result and osm_result.get("name"):
        gvr_by_name = await gvr_cache.query_water_body_by_name(
            osm_result["name"]
        )
        if gvr_by_name and gvr_by_name.get("has_data"):
            gvr_by_name["name"] = osm_result.get("name") or gvr_by_name.get("name")
            gvr_by_name["water_type"] = osm_result.get("water_type") or gvr_by_name.get("water_type")
            result = _build_result(lat, lon, gvr_by_name)
            await cache_set(key, result)
            logger.info(
                "depth_resolver_osm_gvr_crossref",
                service="depth-service",
                action="depth_resolver",
                lat=lat,
                lon=lon,
                name=osm_result["name"],
            )
            return result

    gvr_result = await gvr_cache.query_water_body(lat, lon)
    if gvr_result and gvr_result.get("has_data"):
        result = _build_result(lat, lon, gvr_result)
        await cache_set(key, result)
        logger.info(
            "depth_resolver_gvr_hit",
            service="depth-service",
            action="depth_resolver",
            lat=lat,
            lon=lon,
            name=gvr_result.get("name"),
        )
        return result

    gebco_result = await query_gebco(lat, lon)
    if gebco_result.get("has_data") and gebco_result.get("depth") is not None:
        gebco_result["name"] = None
        gebco_result["water_type"] = None
        gebco_result["depth_type"] = "point"
        result = _build_result(lat, lon, gebco_result)
        await cache_set(key, result)
        logger.info(
            "depth_resolver_gebco_hit",
            service="depth-service",
            action="depth_resolver",
            lat=lat,
            lon=lon,
            depth=result.get("depth"),
        )
        return result

    fallback_result = _no_data(lat, lon)
    if osm_result:
        fallback_result["water_body_name"] = osm_result.get("name")
        fallback_result["water_body_type"] = osm_result.get("water_type")
    elif gvr_result:
        fallback_result["water_body_name"] = gvr_result.get("name")
        fallback_result["water_body_type"] = gvr_result.get("water_type")

    await cache_set(key, fallback_result)
    logger.info(
        "depth_resolver_no_data",
        service="depth-service",
        action="depth_resolver",
        lat=lat,
        lon=lon,
        water_body=fallback_result.get("water_body_name"),
    )
    return fallback_result


def _build_result(lat: float, lon: float, source_data: dict) -> dict:
    depth = source_data.get("depth")
    has_data = source_data.get("has_data", False)

    return {
        "depth": round(depth, 1) if depth is not None else None,
        "depth_display": f"{depth:.1f} м" if depth is not None else None,
        "source": source_data.get("source"),
        "accuracy_m": source_data.get("accuracy_m"),
        "has_data": has_data,
        "lat": lat,
        "lon": lon,
        "water_body_name": source_data.get("name"),
        "water_body_type": source_data.get("water_type"),
        "depth_type": source_data.get("depth_type"),
    }
