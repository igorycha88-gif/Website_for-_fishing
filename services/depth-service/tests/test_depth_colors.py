
from app.services.depth_colors import (
    depth_to_color,
    hex_to_rgb,
    get_color_ramp,
    depth_category_label,
    COLOR_SCHEMES,
)


class TestDepthToColor:
    def test_shallow_navionics(self):
        color = depth_to_color(1.5, "navionics")
        assert color == "#B3E5FC"

    def test_medium_navionics(self):
        color = depth_to_color(7.0, "navionics")
        assert color == "#0288D1"

    def test_deep_navionics(self):
        color = depth_to_color(30.0, "navionics")
        assert color == "#1A237E"

    def test_very_deep(self):
        color = depth_to_color(100.0, "navionics")
        assert color == "#000C2E"

    def test_boundary_2m(self):
        color = depth_to_color(2.0, "navionics")
        assert color == "#4FC3F7"

    def test_boundary_5m(self):
        color = depth_to_color(5.0, "navionics")
        assert color == "#0288D1"

    def test_contrast_scheme(self):
        color = depth_to_color(7.0, "contrast")
        assert color == "#00ACC1"

    def test_sport_scheme(self):
        color = depth_to_color(7.0, "sport")
        assert color == "#43A047"

    def test_unknown_scheme_falls_back(self):
        color = depth_to_color(7.0, "nonexistent")
        assert color == "#0288D1"

    def test_all_schemes_have_6_ranges(self):
        for name, ramp in COLOR_SCHEMES.items():
            assert len(ramp) == 6, f"Scheme {name} should have 6 ranges"


class TestHexToRgb:
    def test_basic(self):
        assert hex_to_rgb("#FF0000") == (255, 0, 0)

    def test_without_hash(self):
        assert hex_to_rgb("00FF00") == (0, 255, 0)

    def test_blue(self):
        assert hex_to_rgb("#0000FF") == (0, 0, 255)


class TestDepthCategoryLabel:
    def test_very_shallow(self):
        assert depth_category_label(1.0) == "0-2\u043c"

    def test_shallow(self):
        assert depth_category_label(3.0) == "2-5\u043c"

    def test_medium(self):
        assert depth_category_label(7.0) == "5-10\u043c"

    def test_deep(self):
        assert depth_category_label(15.0) == "10-20\u043c"

    def test_very_deep(self):
        assert depth_category_label(30.0) == "20-50\u043c"

    def test_extreme(self):
        assert depth_category_label(100.0) == ">50\u043c"


class TestGetColorRamp:
    def test_navionics_ramp(self):
        ramp = get_color_ramp("navionics")
        assert len(ramp) == 6

    def test_invalid_scheme_returns_default(self):
        ramp = get_color_ramp("invalid")
        assert ramp == get_color_ramp("navionics")
