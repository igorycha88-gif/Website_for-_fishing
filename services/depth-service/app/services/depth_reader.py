import math
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_DEPTHIAS_SOURCE = "GEBCO_2024"
_DEPTHIAS_ACCURACY_M = 463

_TILES_DIR = None
_RASTER_DATA = None

_LAND_BG_RATIO_THRESHOLD = 0.7

_DEPTH_RAMP = [
    (80, 6000.0),
    (200, 4000.0),
    (350, 2500.0),
    (400, 1500.0),
    (500, 500.0),
    (600, 200.0),
    (650, 80.0),
    (700, 30.0),
    (800, 10.0),
    (1000, 3.0),
]


def _init_tiles_dir():
    global _TILES_DIR
    tiles_dir = Path(settings.GEBCO_GEOTIFF_PATH).parent / "tiles" if settings.GEBCO_GEOTIFF_PATH else None
    if tiles_dir and tiles_dir.exists():
        _TILES_DIR = tiles_dir
        logger.info("depth_reader_init_tiles", service="depth-service", tiles_dir=str(tiles_dir))
    else:
        _TILES_DIR = None
        logger.info("depth_reader_no_tiles_dir", service="depth-service")


_init_tiles_dir()


def _web_mercator_to_lat_lon(x: float, y: float) -> tuple[float, float]:
    lon = math.degrees(x / 6378137.0)
    lat = math.degrees(math.atan(math.sinh(y / 6378137.0)))
    return lat, lon


def _tile_to_bbox(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    n = 2 ** z
    lon_min = x / n * 360.0 - 180.0
    lon_max = (x + 1) / n * 360.0 - 180.0
    lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return lon_min, lat_min, lon_max, lat_max


async def query_depth(lat: float, lon: float) -> dict:
    logger.info(
        "depth_point_query_start",
        service="depth-service",
        action="depth_point_query",
        lat=lat,
        lon=lon,
    )

    if _RASTER_DATA is not None:
        result = _query_local_raster(lat, lon)
    else:
        result = await _query_gebco_api(lat, lon)

    logger.info(
        "depth_point_query_completed",
        service="depth-service",
        action="depth_point_query",
        lat=lat,
        lon=lon,
        depth=result.get("depth"),
        has_data=result.get("has_data"),
    )
    return result


def _query_local_raster(lat: float, lon: float) -> dict:
    try:
        row, col = _RASTER_DATA["transform"].get_coord(lat, lon)
        data = _RASTER_DATA["band"]
        if 0 <= row < data.shape[0] and 0 <= col < data.shape[1]:
            depth_val = float(data[row, col])
            return {
                "depth": depth_val,
                "source": _DEPTHIAS_SOURCE,
                "accuracy_m": _DEPTHIAS_ACCURACY_M,
                "has_data": True,
            }
    except Exception as e:
        logger.error("depth_local_raster_error", service="depth-service", error=str(e), exc_info=True)

    return {
        "depth": None,
        "source": _DEPTHIAS_SOURCE,
        "accuracy_m": _DEPTHIAS_ACCURACY_M,
        "has_data": False,
    }


def _estimate_depth_from_pixel(r: int, g: int, b: int) -> float | None:
    bg_ratio = b / max(g, 1)
    if bg_ratio < _LAND_BG_RATIO_THRESHOLD:
        return None

    if r >= 250 and g >= 250 and b >= 250:
        return None

    brightness = r + g + b

    for i, (threshold, depth) in enumerate(_DEPTH_RAMP):
        if brightness <= threshold:
            if i == 0:
                return depth
            prev_threshold, prev_depth = _DEPTH_RAMP[i - 1]
            ratio = (brightness - prev_threshold) / max(threshold - prev_threshold, 1)
            return prev_depth + ratio * (depth - prev_depth)

    return _DEPTH_RAMP[-1][1]


def _estimate_depth_from_image(image_bytes: bytes) -> float | None:
    try:
        img = Image.open(BytesIO(image_bytes))
        cx, cy = img.size[0] // 2, img.size[1] // 2
        pixel = img.getpixel((cx, cy))

        if len(pixel) >= 4 and pixel[3] == 0:
            return None

        r, g, b = pixel[0], pixel[1], pixel[2]
        depth = _estimate_depth_from_pixel(r, g, b)
        logger.info(
            "depth_pixel_analyzed",
            service="depth-service",
            action="depth_pixel_analysis",
            r=r,
            g=g,
            b=b,
            estimated_depth=depth,
        )
        return depth
    except Exception as e:
        logger.warning(
            "depth_image_parse_error",
            service="depth-service",
            error=str(e),
        )
        return None


async def _query_gebco_api(lat: float, lon: float) -> dict:
    try:
        margin = 0.005
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetMap",
                "LAYERS": settings.GEBCO_QUERY_LAYER,
                "SRS": "EPSG:4326",
                "BBOX": f"{lon - margin},{lat - margin},{lon + margin},{lat + margin}",
                "WIDTH": 3,
                "HEIGHT": 3,
                "FORMAT": "image/tiff",
                "TRANSPARENT": "TRUE",
            }
            resp = await client.get(settings.GEBCO_WMS_URL, params=params)

            if resp.status_code == 200 and "image" in resp.headers.get("content-type", ""):
                depth = _estimate_depth_from_image(resp.content)
                if depth is not None:
                    logger.info(
                        "depth_gebco_api_result",
                        service="depth-service",
                        action="depth_point_query",
                        lat=lat,
                        lon=lon,
                        depth=depth,
                    )
                    return {
                        "depth": depth,
                        "source": _DEPTHIAS_SOURCE,
                        "accuracy_m": _DEPTHIAS_ACCURACY_M,
                        "has_data": True,
                    }

            logger.warning(
                "depth_gebco_api_no_data",
                service="depth-service",
                action="depth_point_query",
                lat=lat,
                lon=lon,
                status_code=resp.status_code,
            )
    except Exception as e:
        logger.warning(
            "depth_gebco_api_unavailable",
            service="depth-service",
            error=str(e),
        )

    return {
        "depth": None,
        "source": _DEPTHIAS_SOURCE,
        "accuracy_m": _DEPTHIAS_ACCURACY_M,
        "has_data": False,
    }


async def fetch_tile(z: int, x: int, y: int, scheme: str = "navionics") -> bytes | None:
    logger.info(
        "depth_tile_request",
        service="depth-service",
        action="depth_tile",
        z=z,
        x=x,
        y=y,
        scheme=scheme,
    )

    cache_dir = Path(settings.TILE_CACHE_DIR) / scheme
    if cache_dir.exists():
        tile_path = cache_dir / f"{z}" / f"{x}" / f"{y}.png"
        if tile_path.exists():
            logger.info(
                "depth_tile_cache_hit",
                service="depth-service",
                action="depth_tile",
                z=z,
                x=x,
                y=y,
            )
            return tile_path.read_bytes()

    if _TILES_DIR is not None:
        tile_path = _TILES_DIR / f"{z}" / f"{x}" / f"{y}.png"
        if tile_path.exists():
            return tile_path.read_bytes()

    raw_tile = await _proxy_gebco_wms(z, x, y)
    if raw_tile is None:
        return None

    if settings.TILE_RECOLOR:
        from app.services.tile_recolor import recolor_tile

        result_tile = recolor_tile(raw_tile, scheme=scheme)
    else:
        result_tile = raw_tile

    try:
        cache_path = cache_dir / f"{z}" / f"{x}" / f"{y}.png"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(result_tile)
    except Exception as e:
        logger.warning(
            "depth_tile_cache_write_error",
            service="depth-service",
            action="depth_tile",
            error=str(e),
        )

    return result_tile


async def _proxy_gebco_wms(z: int, x: int, y: int) -> bytes | None:
    lon_min, lat_min, lon_max, lat_max = _tile_to_bbox(z, x, y)
    bbox = f"{lon_min},{lat_min},{lon_max},{lat_max}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetMap",
                "LAYERS": settings.GEBCO_WMS_LAYER,
                "SRS": "EPSG:4326",
                "BBOX": bbox,
                "WIDTH": "256",
                "HEIGHT": "256",
                "FORMAT": "image/png",
                "TRANSPARENT": "TRUE",
            }
            resp = await client.get(settings.GEBCO_WMS_URL, params=params)

            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                logger.info(
                    "depth_tile_proxy_ok",
                    service="depth-service",
                    action="depth_tile",
                    z=z,
                    x=x,
                    y=y,
                )
                return resp.content

            logger.warning(
                "depth_tile_proxy_fail",
                service="depth-service",
                action="depth_tile",
                z=z,
                x=x,
                y=y,
                status_code=resp.status_code,
            )
    except Exception as e:
        logger.warning(
            "depth_tile_proxy_error",
            service="depth-service",
            action="depth_tile",
            z=z,
            x=x,
            y=y,
            error=str(e),
        )

    return None
