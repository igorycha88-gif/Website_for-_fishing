from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealth:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "depth-service"
        assert data["data_source"] == "GEBCO + OSM + GVR"


class TestDepthEstimation:
    def test_deep_water_pixel(self):
        from app.services.depth_reader import _estimate_depth_from_pixel
        depth = _estimate_depth_from_pixel(0, 10, 59)
        assert depth is not None
        assert depth > 4000

    def test_medium_water_pixel(self):
        from app.services.depth_reader import _estimate_depth_from_pixel
        depth = _estimate_depth_from_pixel(32, 178, 219)
        assert depth is not None
        assert 1000 < depth < 3000

    def test_shallow_water_pixel(self):
        from app.services.depth_reader import _estimate_depth_from_pixel
        depth = _estimate_depth_from_pixel(211, 255, 237)
        assert depth is not None
        assert depth < 30

    def test_land_pixel_returns_none(self):
        from app.services.depth_reader import _estimate_depth_from_pixel
        depth = _estimate_depth_from_pixel(70, 207, 108)
        assert depth is None

    def test_white_pixel_returns_none(self):
        from app.services.depth_reader import _estimate_depth_from_pixel
        depth = _estimate_depth_from_pixel(255, 255, 255)
        assert depth is None

    def test_very_shallow_water(self):
        from app.services.depth_reader import _estimate_depth_from_pixel
        depth = _estimate_depth_from_pixel(162, 248, 236)
        assert depth is not None
        assert depth < 100

    def test_deeper_shallower_monotonic(self):
        from app.services.depth_reader import _estimate_depth_from_pixel
        deep = _estimate_depth_from_pixel(23, 124, 191)
        shallow = _estimate_depth_from_pixel(211, 255, 237)
        assert deep > shallow

    def test_image_parsing_center_pixel(self):
        import io
        from PIL import Image
        from app.services.depth_reader import _estimate_depth_from_image
        img = Image.new("RGB", (3, 3), (32, 178, 219))
        buf = io.BytesIO()
        img.save(buf, format="TIFF")
        depth = _estimate_depth_from_image(buf.getvalue())
        assert depth is not None
        assert 1000 < depth < 3000

    def test_image_parsing_land_pixel(self):
        import io
        from PIL import Image
        from app.services.depth_reader import _estimate_depth_from_image
        img = Image.new("RGB", (3, 3), (70, 207, 108))
        buf = io.BytesIO()
        img.save(buf, format="TIFF")
        depth = _estimate_depth_from_image(buf.getvalue())
        assert depth is None

    def test_image_invalid_bytes_returns_none(self):
        from app.services.depth_reader import _estimate_depth_from_image
        assert _estimate_depth_from_image(b"not an image") is None


class TestDepthPoint:
    @patch("app.api.v1.endpoints.depth.resolve_depth", new_callable=AsyncMock)
    def test_depth_point_with_data(self, mock_resolve):
        mock_resolve.return_value = {
            "depth": 4000.0,
            "depth_display": "4000.0 м",
            "source": "GEBCO",
            "accuracy_m": 463,
            "has_data": True,
            "lat": 43.0,
            "lon": 36.0,
            "water_body_name": None,
            "water_body_type": None,
            "depth_type": "point",
        }
        response = client.get("/api/v1/depth/point", params={"lat": 43.0, "lon": 36.0})
        assert response.status_code == 200
        data = response.json()
        assert data["has_data"] is True
        assert data["depth"] == 4000.0
        assert data["depth_display"] == "4000.0 м"
        assert data["lat"] == 43.0
        assert data["lon"] == 36.0
        assert "season" in data
        assert isinstance(data["fish_match"], list)

    @patch("app.api.v1.endpoints.depth.resolve_depth", new_callable=AsyncMock)
    def test_depth_point_no_data_land(self, mock_resolve):
        mock_resolve.return_value = {
            "depth": None,
            "depth_display": None,
            "source": None,
            "accuracy_m": None,
            "has_data": False,
            "lat": 57.22,
            "lon": 37.84,
            "water_body_name": None,
            "water_body_type": None,
            "depth_type": None,
        }
        response = client.get("/api/v1/depth/point", params={"lat": 57.22, "lon": 37.84})
        assert response.status_code == 200
        data = response.json()
        assert data["has_data"] is False
        assert data["depth"] is None
        assert data["depth_display"] is None
        assert data["fish_match"] == []

    @patch("app.api.v1.endpoints.depth.resolve_depth", new_callable=AsyncMock)
    def test_depth_point_shallow_with_fish(self, mock_resolve):
        mock_resolve.return_value = {
            "depth": 3.0,
            "depth_display": "3.0 м",
            "source": "OSM",
            "accuracy_m": 50,
            "has_data": True,
            "lat": 55.0,
            "lon": 10.0,
            "water_body_name": "Test Lake",
            "water_body_type": "lake",
            "depth_type": "max",
        }
        response = client.get("/api/v1/depth/point", params={"lat": 55.0, "lon": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert data["has_data"] is True
        assert len(data["fish_match"]) > 0
        assert data["source"] == "OSM"
        assert data["water_body_name"] == "Test Lake"
        assert data["water_body_type"] == "lake"
        assert data["depth_type"] == "max"

    @patch("app.api.v1.endpoints.depth.resolve_depth", new_callable=AsyncMock)
    def test_depth_point_gvr_source(self, mock_resolve):
        mock_resolve.return_value = {
            "depth": 230.0,
            "depth_display": "230.0 м",
            "source": "GVR",
            "accuracy_m": 100,
            "has_data": True,
            "lat": 60.0,
            "lon": 31.0,
            "water_body_name": "Ладожское озеро",
            "water_body_type": "lake",
            "depth_type": "max",
        }
        response = client.get("/api/v1/depth/point", params={"lat": 60.0, "lon": 31.0})
        assert response.status_code == 200
        data = response.json()
        assert data["has_data"] is True
        assert data["source"] == "GVR"
        assert data["water_body_name"] == "Ладожское озеро"
        assert data["depth"] == 230.0

    @patch("app.api.v1.endpoints.depth.resolve_depth", new_callable=AsyncMock)
    def test_depth_point_response_structure(self, mock_resolve):
        mock_resolve.return_value = {
            "depth": None,
            "depth_display": None,
            "source": None,
            "accuracy_m": None,
            "has_data": False,
            "lat": 60.0,
            "lon": 30.0,
            "water_body_name": None,
            "water_body_type": None,
            "depth_type": None,
        }
        response = client.get("/api/v1/depth/point", params={"lat": 60.0, "lon": 30.0})
        data = response.json()
        required_fields = [
            "depth", "depth_display", "category", "source",
            "accuracy_m", "has_data", "lat", "lon", "season", "fish_match",
            "water_body_name", "water_body_type", "depth_type",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_depth_point_invalid_lat(self):
        response = client.get("/api/v1/depth/point", params={"lat": 91, "lon": 37})
        assert response.status_code == 422

    def test_depth_point_invalid_lon(self):
        response = client.get("/api/v1/depth/point", params={"lat": 55, "lon": 181})
        assert response.status_code == 422

    def test_depth_point_missing_lat(self):
        response = client.get("/api/v1/depth/point", params={"lon": 37})
        assert response.status_code == 422


class TestDepthTiles:
    def test_tile_endpoint_returns_png(self):
        response = client.get("/api/v1/depth/tiles/5/20/10.png")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_tile_invalid_zoom(self):
        response = client.get("/api/v1/depth/tiles/19/0/0.png")
        assert response.status_code == 422

    def test_tile_valid_zoom_zero(self):
        response = client.get("/api/v1/depth/tiles/0/0/0.png")
        assert response.status_code == 200


class TestFishMatcher:
    def test_match_fish_shallow_depth_summer(self):
        from app.services.fish_matcher import match_fish_by_depth
        matches = match_fish_by_depth(2.0, "summer")
        names = [m["name"] for m in matches]
        assert "Щука" in names
        assert "Карась" in names

    def test_match_fish_deep_depth(self):
        from app.services.fish_matcher import match_fish_by_depth
        matches = match_fish_by_depth(8.0, "summer")
        names = [m["name"] for m in matches]
        assert "Судак" in names

    def test_match_fish_no_match(self):
        from app.services.fish_matcher import match_fish_by_depth
        matches = match_fish_by_depth(100.0, "summer")
        assert len(matches) == 0

    def test_match_fish_negative_depth(self):
        from app.services.fish_matcher import match_fish_by_depth
        matches = match_fish_by_depth(-1.0, "summer")
        assert len(matches) == 0

    def test_match_fish_none_depth(self):
        from app.services.fish_matcher import match_fish_by_depth
        matches = match_fish_by_depth(None, "summer")
        assert len(matches) == 0

    def test_match_fish_returns_structure(self):
        from app.services.fish_matcher import match_fish_by_depth
        matches = match_fish_by_depth(3.0, "summer")
        for m in matches:
            assert "name" in m
            assert "icon" in m
            assert "depth_range" in m
            assert "season" in m

    def test_get_depth_category(self):
        from app.services.fish_matcher import get_depth_category
        assert get_depth_category(1.0) == "Очень мелко"
        assert get_depth_category(3.0) == "Мелководье"
        assert get_depth_category(7.0) == "Средняя глубина"
        assert get_depth_category(15.0) == "Глубоко"
        assert get_depth_category(30.0) == "Очень глубоко"

    def test_get_season(self):
        from app.services.fish_matcher import get_season
        assert get_season(1) == "winter"
        assert get_season(4) == "spring"
        assert get_season(7) == "summer"
        assert get_season(10) == "autumn"
