
from app.services.tile_recolor import recolor_tile, _estimate_depth_from_pixel, _depth_to_scheme_rgb


def _make_png(r: int, g: int, b: int) -> bytes:
    from PIL import Image
    from io import BytesIO

    img = Image.new("RGBA", (4, 4), (r, g, b, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestEstimateDepthFromPixel:
    def test_deep_water(self):
        depth = _estimate_depth_from_pixel(0, 10, 59)
        assert depth is not None
        assert depth > 4000

    def test_shallow_water(self):
        depth = _estimate_depth_from_pixel(200, 220, 240)
        assert depth is not None
        assert depth < 100

    def test_land_returns_none(self):
        depth = _estimate_depth_from_pixel(100, 150, 100)
        assert depth is None

    def test_white_returns_none(self):
        depth = _estimate_depth_from_pixel(255, 255, 255)
        assert depth is None


class TestDepthToSchemeRGB:
    def test_shallow_navionics(self):
        rgb = _depth_to_scheme_rgb(1.0, "navionics")
        assert rgb == (179, 229, 252)

    def test_deep_navionics(self):
        rgb = _depth_to_scheme_rgb(30.0, "navionics")
        assert rgb == (26, 35, 126)


class TestRecolorTile:
    def test_water_pixel_gets_colored(self):
        raw = _make_png(0, 10, 59)
        result = recolor_tile(raw, "navionics")
        assert result is not None
        assert len(result) > 0
        assert result[:4] == b"\x89PNG"

    def test_land_pixel_gets_transparent(self):
        raw = _make_png(100, 150, 100)
        result = recolor_tile(raw, "navionics")
        assert result is not None
        assert result[:4] == b"\x89PNG"

    def test_invalid_input_returns_raw(self):
        raw = b"not_a_png"
        result = recolor_tile(raw, "navionics")
        assert result == raw
