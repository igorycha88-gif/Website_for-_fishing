from unittest.mock import AsyncMock, patch

import pytest

from app.services import depth_resolver


class TestDepthResolver:
    @pytest.mark.asyncio
    @patch("app.services.depth_resolver.cache_get", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.cache_set", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.osm_overpass_client.query_water_body", new_callable=AsyncMock)
    async def test_osm_source_with_depth(self, mock_osm, mock_cache_set, mock_cache_get):
        mock_cache_get.return_value = None
        mock_osm.return_value = {
            "name": "Озеро Сенеж",
            "water_type": "lake",
            "depth": 6.0,
            "depth_type": "avg",
            "source": "OSM",
            "accuracy_m": 50,
            "has_data": True,
        }

        result = await depth_resolver.resolve_depth(56.16, 37.03)

        assert result["has_data"] is True
        assert result["depth"] == 6.0
        assert result["source"] == "OSM"
        assert result["water_body_name"] == "Озеро Сенеж"
        assert result["water_body_type"] == "lake"
        mock_cache_set.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.depth_resolver.cache_get", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.cache_set", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.osm_overpass_client.query_water_body", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.gvr_cache.query_water_body_by_name", new_callable=AsyncMock)
    async def test_osm_name_gvr_crossref(self, mock_gvr_name, mock_osm, mock_cache_set, mock_cache_get):
        mock_cache_get.return_value = None
        mock_osm.return_value = {
            "name": "Ладожское озеро",
            "water_type": "lake",
            "depth": None,
            "depth_type": None,
            "source": "OSM",
            "accuracy_m": 50,
            "has_data": False,
        }
        mock_gvr_name.return_value = {
            "name": "Ладожское озеро",
            "water_type": "lake",
            "depth": 230.0,
            "depth_type": "max",
            "source": "GVR",
            "accuracy_m": 100,
            "has_data": True,
        }

        result = await depth_resolver.resolve_depth(60.0, 31.0)

        assert result["has_data"] is True
        assert result["depth"] == 230.0
        assert result["source"] == "GVR"
        assert result["water_body_name"] == "Ладожское озеро"
        mock_gvr_name.assert_called_once_with("Ладожское озеро")

    @pytest.mark.asyncio
    @patch("app.services.depth_resolver.cache_get", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.cache_set", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.osm_overpass_client.query_water_body", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.gvr_cache.query_water_body", new_callable=AsyncMock)
    async def test_fallback_to_gvr_bbox(self, mock_gvr, mock_osm, mock_cache_set, mock_cache_get):
        mock_cache_get.return_value = None
        mock_osm.return_value = None
        mock_gvr.return_value = {
            "name": "Озеро Плещеево",
            "water_type": "lake",
            "depth": 24.0,
            "depth_type": "max",
            "source": "GVR",
            "accuracy_m": 100,
            "has_data": True,
        }

        result = await depth_resolver.resolve_depth(56.80, 38.82)

        assert result["has_data"] is True
        assert result["depth"] == 24.0
        assert result["source"] == "GVR"
        assert result["water_body_name"] == "Озеро Плещеево"

    @pytest.mark.asyncio
    @patch("app.services.depth_resolver.cache_get", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.cache_set", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.osm_overpass_client.query_water_body", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.gvr_cache.query_water_body", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.query_gebco", new_callable=AsyncMock)
    async def test_fallback_to_gebco(self, mock_gebco, mock_gvr, mock_osm, mock_cache_set, mock_cache_get):
        mock_cache_get.return_value = None
        mock_osm.return_value = None
        mock_gvr.return_value = None
        mock_gebco.return_value = {
            "depth": 2000.0,
            "source": "GEBCO_2024",
            "accuracy_m": 463,
            "has_data": True,
        }

        result = await depth_resolver.resolve_depth(44.6, 33.5)

        assert result["has_data"] is True
        assert result["depth"] == 2000.0
        assert result["source"] == "GEBCO_2024"

    @pytest.mark.asyncio
    @patch("app.services.depth_resolver.cache_get", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.cache_set", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.osm_overpass_client.query_water_body", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.gvr_cache.query_water_body", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.query_gebco", new_callable=AsyncMock)
    async def test_all_sources_fail(self, mock_gebco, mock_gvr, mock_osm, mock_cache_set, mock_cache_get):
        mock_cache_get.return_value = None
        mock_osm.return_value = None
        mock_gvr.return_value = None
        mock_gebco.return_value = {
            "depth": None,
            "source": "GEBCO_2024",
            "accuracy_m": 463,
            "has_data": False,
        }

        result = await depth_resolver.resolve_depth(0.0, 0.0)

        assert result["has_data"] is False
        assert result["depth"] is None
        assert result["source"] is None
        assert result["water_body_name"] is None

    @pytest.mark.asyncio
    @patch("app.services.depth_resolver.cache_get", new_callable=AsyncMock)
    async def test_cache_hit(self, mock_cache_get):
        mock_cache_get.return_value = {
            "depth": 5.0,
            "depth_display": "5.0 м",
            "source": "OSM",
            "accuracy_m": 50,
            "has_data": True,
            "lat": 56.16,
            "lon": 37.03,
            "water_body_name": "Озеро Сенеж",
            "water_body_type": "lake",
            "depth_type": "avg",
        }

        result = await depth_resolver.resolve_depth(56.16, 37.03)

        assert result["has_data"] is True
        assert result["depth"] == 5.0
        assert result["water_body_name"] == "Озеро Сенеж"

    @pytest.mark.asyncio
    @patch("app.services.depth_resolver.cache_get", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.cache_set", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.osm_overpass_client.query_water_body", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.gvr_cache.query_water_body", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.query_gebco", new_callable=AsyncMock)
    async def test_osm_name_no_gvr_depth_keeps_name(self, mock_gebco, mock_gvr, mock_osm, mock_cache_set, mock_cache_get):
        mock_cache_get.return_value = None
        mock_osm.return_value = {
            "name": "Безымянное озеро",
            "water_type": "lake",
            "depth": None,
            "depth_type": None,
            "source": "OSM",
            "accuracy_m": 50,
            "has_data": False,
        }
        mock_gvr.return_value = None
        mock_gebco.return_value = {
            "depth": None,
            "source": "GEBCO_2024",
            "accuracy_m": 463,
            "has_data": False,
        }

        result = await depth_resolver.resolve_depth(60.0, 30.0)

        assert result["has_data"] is False
        assert result["water_body_name"] == "Безымянное озеро"
        assert result["water_body_type"] == "lake"

    @pytest.mark.asyncio
    @patch("app.services.depth_resolver.cache_get", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.cache_set", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.osm_overpass_client.query_water_body", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.gvr_cache.query_water_body", new_callable=AsyncMock)
    @patch("app.services.depth_resolver.query_gebco", new_callable=AsyncMock)
    async def test_gebco_depth_with_depth_type_point(self, mock_gebco, mock_gvr, mock_osm, mock_cache_set, mock_cache_get):
        mock_cache_get.return_value = None
        mock_osm.return_value = None
        mock_gvr.return_value = None
        mock_gebco.return_value = {
            "depth": 500.0,
            "source": "GEBCO_2024",
            "accuracy_m": 463,
            "has_data": True,
        }

        result = await depth_resolver.resolve_depth(44.0, 38.0)

        assert result["has_data"] is True
        assert result["depth"] == 500.0
        assert result["depth_type"] == "point"
        assert result["water_body_name"] is None
