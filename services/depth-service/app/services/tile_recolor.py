from io import BytesIO

from PIL import Image

from app.core.logging_config import get_logger
from app.services.depth_colors import hex_to_rgb, get_color_ramp

logger = get_logger(__name__)

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


def _depth_to_scheme_rgb(depth: float, scheme: str = "navionics") -> tuple[int, int, int]:
    ramp = get_color_ramp(scheme)
    for min_d, max_d, hex_color in ramp:
        if min_d <= depth < max_d:
            return hex_to_rgb(hex_color)
    return hex_to_rgb(ramp[-1][2])


def recolor_tile(raw_png: bytes, scheme: str = "navionics") -> bytes:
    try:
        img = Image.open(BytesIO(raw_png)).convert("RGBA")
        pixels = img.load()
        w, h = img.size

        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                if a == 0:
                    continue

                depth = _estimate_depth_from_pixel(r, g, b)
                if depth is None:
                    pixels[x, y] = (0, 0, 0, 0)
                else:
                    nr, ng, nb = _depth_to_scheme_rgb(depth, scheme)
                    pixels[x, y] = (nr, ng, nb, 180)

        output = BytesIO()
        img.save(output, format="PNG", optimize=True)
        result = output.getvalue()

        logger.info(
            "tile_recolored",
            service="depth-service",
            action="tile_recolor",
            size=len(result),
            scheme=scheme,
        )
        return result

    except Exception as e:
        logger.warning(
            "tile_recolor_error",
            service="depth-service",
            action="tile_recolor",
            error=str(e),
        )
        return raw_png
