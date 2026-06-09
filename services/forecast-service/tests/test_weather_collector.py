import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime, date
from decimal import Decimal

from app.services.weather_collector import WeatherCollectorService
from app.models.forecast import Region


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def mock_regions():
    region1 = Region(
        id=uuid4(),
        name="Москва",
        code="MOW",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
        timezone="Europe/Moscow",
        is_active=True,
    )
    region2 = Region(
        id=uuid4(),
        name="Санкт-Петербург",
        code="SPE",
        latitude=Decimal("59.9343"),
        longitude=Decimal("30.3351"),
        timezone="Europe/Moscow",
        is_active=True,
    )
    return [region1, region2]


@pytest.fixture
def mock_forecast_response():
    return {
        "city": {
            "sunrise": 1708300000,
            "sunset": 1708340000,
        },
        "list": [
            {
                "dt": 1708300800,
                "main": {
                    "temp": 5.5,
                    "feels_like": 2.3,
                    "pressure": 1013,
                    "humidity": 75,
                },
                "wind": {
                    "speed": 3.5,
                    "deg": 180,
                    "gust": 5.0,
                },
                "clouds": {"all": 50},
                "rain": {"1h": 0.5},
                "pop": 0.3,
                "weather": [{"main": "Rain", "icon": "10d"}],
                "visibility": 10000,
            },
            {
                "dt": 1708304400,
                "main": {
                    "temp": 6.0,
                    "feels_like": 3.0,
                    "pressure": 1015,
                    "humidity": 70,
                },
                "wind": {
                    "speed": 4.0,
                    "deg": 200,
                },
                "clouds": {"all": 40},
                "pop": 0.1,
                "weather": [{"main": "Clouds", "icon": "04d"}],
                "visibility": 10000,
            },
        ],
    }


class TestWeatherCollectorService:
    def test_init(self, mock_db):
        service = WeatherCollectorService(mock_db)
        assert service.db == mock_db
        assert service.batch_delay == 0.5

    @pytest.mark.asyncio
    async def test_collect_all_regions_no_regions(self, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = WeatherCollectorService(mock_db)
        result = await service.collect_all_regions()

        assert result["status"] == "error"
        assert result["message"] == "No active regions"
        assert result["collected"] == 0

    @pytest.mark.asyncio
    async def test_collect_all_regions_success(
        self, mock_db, mock_regions, mock_forecast_response
    ):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_regions
        mock_db.execute.return_value = mock_result

        service = WeatherCollectorService(mock_db)

        with patch.object(
            service, "_fetch_forecast_from_api", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_forecast_response

            result = await service.collect_all_regions(days=1)

        assert result["status"] == "success"
        assert result["collected"] == 2
        assert result["total_regions"] == 2
        assert result["total_records"] == 4
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_collect_all_regions_partial_error(self, mock_db, mock_regions):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_regions
        mock_db.execute.return_value = mock_result

        service = WeatherCollectorService(mock_db)

        call_count = 0

        async def side_effect_fetch(lat, lon, days):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "city": {"sunrise": 1708300000, "sunset": 1708340000},
                    "list": [],
                }
            raise Exception("API Error")

        with patch.object(
            service, "_fetch_forecast_from_api", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = side_effect_fetch

            result = await service.collect_all_regions(days=1)

        assert result["status"] == "success"
        assert result["collected"] == 1
        assert len(result["errors"]) == 1

    @pytest.mark.asyncio
    async def test_fetch_forecast_from_api_success(self, mock_db):
        service = WeatherCollectorService(mock_db)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"city": {}, "list": []}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await service._fetch_forecast_from_api(55.75, 37.61, days=1)

        assert result is not None
        assert "city" in result
        assert "list" in result

    @pytest.mark.asyncio
    async def test_fetch_forecast_from_api_error(self, mock_db):
        service = WeatherCollectorService(mock_db)

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await service._fetch_forecast_from_api(55.75, 37.61, days=1)

        assert result is None

    @pytest.mark.asyncio
    async def test_save_weather_data_success(self, mock_db, mock_forecast_response):
        service = WeatherCollectorService(mock_db)
        region_id = uuid4()

        result = await service._save_weather_data(region_id, mock_forecast_response)

        assert result == 2
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_weather_data_empty_list(self, mock_db):
        service = WeatherCollectorService(mock_db)
        region_id = uuid4()

        result = await service._save_weather_data(region_id, {"city": {}, "list": []})

        assert result == 0
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_collect_single_region_not_found(self, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = WeatherCollectorService(mock_db)
        result = await service.collect_single_region(uuid4())

        assert result["status"] == "error"
        assert result["message"] == "Region not found"

    @pytest.mark.asyncio
    async def test_collect_single_region_success(
        self, mock_db, mock_regions, mock_forecast_response
    ):
        region = mock_regions[0]
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = region
        mock_db.execute.return_value = mock_result

        service = WeatherCollectorService(mock_db)

        with patch.object(
            service, "_fetch_forecast_from_api", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_forecast_response

            result = await service.collect_single_region(region.id, days=1)

        assert result["status"] == "success"
        assert result["region"] == region.name
        assert result["records_saved"] == 2

    @pytest.mark.asyncio
    async def test_collect_single_region_error(self, mock_db, mock_regions):
        region = mock_regions[0]
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = region
        mock_db.execute.return_value = mock_result

        service = WeatherCollectorService(mock_db)

        with patch.object(
            service, "_fetch_forecast_from_api", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = None

            result = await service.collect_single_region(region.id, days=1)

        assert result["status"] == "error"
        assert "error" in result
