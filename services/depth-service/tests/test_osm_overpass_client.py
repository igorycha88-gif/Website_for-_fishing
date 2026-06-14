from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services import osm_overpass_client


class TestParseWaterType:
    def test_lake(self):
        assert osm_overpass_client._parse_water_type({"water": "lake"}) == "lake"

    def test_reservoir(self):
        assert osm_overpass_client._parse_water_type({"water": "reservoir"}) == "reservoir"

    def test_river(self):
        assert osm_overpass_client._parse_water_type({"water": "river"}) == "river"

    def test_riverbank(self):
        assert osm_overpass_client._parse_water_type({"waterway": "riverbank"}) == "river"

    def test_natural_water_no_subtype(self):
        assert osm_overpass_client._parse_water_type({"natural": "water"}) == "lake"

    def test_no_tags(self):
        assert osm_overpass_client._parse_water_type({}) is None


class TestParseDepth:
    def test_depth_avg(self):
        depth, dtype = osm_overpass_client._parse_depth({"depth": "5.5"})
        assert depth == 5.5
        assert dtype == "avg"

    def test_depth_max(self):
        depth, dtype = osm_overpass_client._parse_depth({"depth:max": "30"})
        assert depth == 30.0
        assert dtype == "max"

    def test_max_depth_alt_tag(self):
        depth, dtype = osm_overpass_client._parse_depth({"max_depth": "12.5"})
        assert depth == 12.5
        assert dtype == "max"

    def test_depth_priority_avg_over_max(self):
        depth, dtype = osm_overpass_client._parse_depth({"depth": "5", "depth:max": "30"})
        assert depth == 5.0
        assert dtype == "avg"

    def test_no_depth(self):
        depth, dtype = osm_overpass_client._parse_depth({})
        assert depth is None
        assert dtype is None

    def test_negative_depth(self):
        depth, dtype = osm_overpass_client._parse_depth({"depth": "-5"})
        assert depth == 5.0
        assert dtype == "avg"

    def test_invalid_depth(self):
        depth, dtype = osm_overpass_client._parse_depth({"depth": "abc"})
        assert depth is None
        assert dtype is None


class TestPickBestElement:
    def test_prefers_element_with_depth(self):
        elements = [
            {"tags": {"name": "Lake A", "area": "100"}},
            {"tags": {"name": "Lake B", "area": "200", "depth": "5"}},
        ]
        result = osm_overpass_client._pick_best_element(elements)
        assert result["name"] == "Lake B"

    def test_prefers_largest_with_name_when_no_depth(self):
        elements = [
            {"tags": {"name": "Small Lake", "area": "50"}},
            {"tags": {"name": "Big Lake", "area": "500"}},
        ]
        result = osm_overpass_client._pick_best_element(elements)
        assert result["name"] == "Big Lake"

    def test_returns_none_for_empty(self):
        assert osm_overpass_client._pick_best_element([]) is None

    def test_returns_first_when_no_name_no_depth(self):
        elements = [{"tags": {"natural": "water"}}]
        result = osm_overpass_client._pick_best_element(elements)
        assert "natural" in result


class TestQueryWaterBody:
    @pytest.mark.asyncio
    async def test_successful_lake_query(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "elements": [
                {
                    "tags": {
                        "name": "Озеро Сенеж",
                        "water": "lake",
                        "depth": "6",
                        "area": "850000",
                    }
                }
            ]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await osm_overpass_client.query_water_body(56.16, 37.03)

        assert result is not None
        assert result["name"] == "Озеро Сенеж"
        assert result["water_type"] == "lake"
        assert result["depth"] == 6.0
        assert result["has_data"] is True
        assert result["source"] == "OSM"

    @pytest.mark.asyncio
    async def test_water_body_without_depth(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "elements": [
                {
                    "tags": {
                        "name": "Малое озеро",
                        "water": "lake",
                    }
                }
            ]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await osm_overpass_client.query_water_body(60.0, 30.0)

        assert result is not None
        assert result["name"] == "Малое озеро"
        assert result["depth"] is None
        assert result["has_data"] is False

    @pytest.mark.asyncio
    async def test_rate_limit_429(self):
        mock_response = MagicMock()
        mock_response.status_code = 429

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await osm_overpass_client.query_water_body(60.0, 30.0)

        assert result is None

    @pytest.mark.asyncio
    async def test_http_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await osm_overpass_client.query_water_body(60.0, 30.0)

        assert result is None

    @pytest.mark.asyncio
    async def test_timeout(self):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await osm_overpass_client.query_water_body(60.0, 30.0)

        assert result is None

    @pytest.mark.asyncio
    async def test_empty_elements(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"elements": []}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await osm_overpass_client.query_water_body(0.0, 0.0)

        assert result is None

    @pytest.mark.asyncio
    async def test_river_waterbody(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "elements": [
                {
                    "tags": {
                        "name": "Волга",
                        "waterway": "riverbank",
                        "max_depth": "15",
                    }
                }
            ]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await osm_overpass_client.query_water_body(55.75, 37.62)

        assert result is not None
        assert result["water_type"] == "river"
        assert result["depth"] == 15.0
        assert result["depth_type"] == "max"
