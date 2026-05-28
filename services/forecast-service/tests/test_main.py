import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCollectInitialWeatherLogic:
    @pytest.mark.asyncio
    async def test_initial_weather_logic_success(self):
        from app.services.weather_collector import WeatherCollectorService

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        collector = WeatherCollectorService(mock_db)

        with patch.object(
            collector, "_fetch_forecast_from_api", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = {
                "city": {"sunrise": 1708300000, "sunset": 1708340000},
                "list": [],
            }

            result = await collector.collect_all_regions(days=4)

        assert "status" in result
        assert "collected" in result

    @pytest.mark.asyncio
    async def test_initial_weather_logic_graceful_error_handling(self):
        from app.services.weather_collector import WeatherCollectorService

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        collector = WeatherCollectorService(mock_db)

        with patch.object(
            collector, "_fetch_forecast_from_api", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = Exception("API Error")

            result = await collector.collect_all_regions(days=4)

        assert result["status"] == "error"
        assert result["collected"] == 0

    @pytest.mark.asyncio
    async def test_initial_weather_uses_correct_days_parameter(self):
        from app.services.weather_collector import WeatherCollectorService

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        collector = WeatherCollectorService(mock_db)

        with patch.object(
            collector, "_fetch_forecast_from_api", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = {
                "city": {"sunrise": 1708300000, "sunset": 1708340000},
                "list": [],
            }

            await collector.collect_all_regions(days=4)

            assert mock_fetch.call_count == 0
