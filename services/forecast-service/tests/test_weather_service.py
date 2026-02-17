import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from datetime import datetime

from app.services.weather import WeatherService


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    return redis


@pytest.fixture
def weather_service(mock_redis):
    return WeatherService(
        api_key="test_api_key",
        base_url="https://api.openweathermap.org/data/2.5",
        redis=mock_redis,
        cache_ttl=3600,
    )


@pytest.fixture
def sample_api_response():
    return {
        "main": {"temp": 15.5, "feels_like": 14.0, "pressure": 1013, "humidity": 75},
        "wind": {"speed": 3.5, "deg": 180, "gust": 5.0},
        "clouds": {"all": 50},
        "weather": [{"main": "Clouds", "description": "облачно", "icon": "03d"}],
        "visibility": 10000,
        "sys": {"sunrise": 1708156800, "sunset": 1708192800},
        "name": "Moscow",
    }


class TestWeatherServiceCacheKey:
    def test_get_cache_key_rounds_coordinates(self, weather_service):
        key = weather_service._get_cache_key(55.755833, 37.617333)
        assert key == "weather:55.7558:37.6173"

    def test_get_cache_key_negative_coordinates(self, weather_service):
        key = weather_service._get_cache_key(-23.5505, -46.6333)
        assert key == "weather:-23.5505:-46.6333"


class TestWeatherServiceCache:
    @pytest.mark.asyncio
    async def test_get_from_cache_hit(self, weather_service, mock_redis):
        cached_data = {"temperature": 10, "humidity": 80}
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_data))

        result = await weather_service._get_from_cache("test_key")

        assert result == cached_data
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_from_cache_miss(self, weather_service, mock_redis):
        mock_redis.get = AsyncMock(return_value=None)

        result = await weather_service._get_from_cache("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_from_cache_error(self, weather_service, mock_redis):
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))

        result = await weather_service._get_from_cache("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_save_to_cache_success(self, weather_service, mock_redis):
        data = {"temperature": 10, "humidity": 80}

        await weather_service._save_to_cache("test_key", data)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "test_key"
        assert call_args[0][1] == 3600
        assert json.loads(call_args[0][2]) == data

    @pytest.mark.asyncio
    async def test_save_to_cache_error(self, weather_service, mock_redis):
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis error"))

        await weather_service._save_to_cache("test_key", {"data": "test"})

        mock_redis.setex.assert_called_once()


class TestWeatherServiceFetchFromAPI:
    @pytest.mark.asyncio
    async def test_fetch_from_api_success(self, weather_service, sample_api_response):
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value=sample_api_response)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await weather_service._fetch_from_api(55.7558, 37.6173)

            assert result is not None
            assert result["temperature"] == 15.5
            assert result["humidity"] == 75
            assert result["wind_speed"] == 3.5
            assert result["weather_condition"] == "Clouds"

    @pytest.mark.asyncio
    async def test_fetch_from_api_unauthorized(self, weather_service):
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await weather_service._fetch_from_api(55.7558, 37.6173)

            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_from_api_not_found(self, weather_service):
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.text = "Not found"
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await weather_service._fetch_from_api(99.9999, 99.9999)

            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_from_api_timeout(self, weather_service):
        import httpx

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await weather_service._fetch_from_api(55.7558, 37.6173)

            assert result is None


class TestWeatherServiceParseResponse:
    def test_parse_full_response(self, weather_service, sample_api_response):
        result = weather_service._parse_weather_response(sample_api_response)

        assert result["temperature"] == 15.5
        assert result["feels_like"] == 14.0
        assert result["pressure_hpa"] == 1013
        assert result["pressure_mmhg"] == 760
        assert result["humidity"] == 75
        assert result["wind_speed"] == 3.5
        assert result["wind_direction"] == 180
        assert result["wind_gust"] == 5.0
        assert result["cloudiness"] == 50
        assert result["weather_condition"] == "Clouds"
        assert result["weather_description"] == "облачно"
        assert result["weather_icon"] == "03d"
        assert result["visibility_m"] == 10000
        assert result["sunrise"] is not None
        assert result["sunset"] is not None
        assert result["city_name"] == "Moscow"

    def test_parse_minimal_response(self, weather_service):
        minimal_data = {
            "main": {"temp": 0},
            "wind": {},
            "clouds": {},
            "weather": [],
            "sys": {},
        }

        result = weather_service._parse_weather_response(minimal_data)

        assert result["temperature"] == 0
        assert result["feels_like"] is None
        assert result["humidity"] is None
        assert result["wind_speed"] is None
        assert result["cloudiness"] is None
        assert result["weather_condition"] is None

    def test_parse_pressure_conversion(self, weather_service):
        data = {
            "main": {"temp": 10, "pressure": 1013},
            "wind": {},
            "clouds": {},
            "weather": [],
            "sys": {},
        }

        result = weather_service._parse_weather_response(data)

        assert result["pressure_mmhg"] == 760


class TestWeatherServiceGetCurrentWeather:
    @pytest.mark.asyncio
    async def test_get_current_weather_cache_hit(self, weather_service, mock_redis):
        cached_data = {"temperature": 10, "humidity": 80}
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_data))

        result = await weather_service.get_current_weather(
            55.7558, 37.6173, use_cache=True
        )

        assert result == cached_data
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_weather_cache_miss_fetch_success(
        self, weather_service, mock_redis, sample_api_response
    ):
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value=sample_api_response)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await weather_service.get_current_weather(
                55.7558, 37.6173, use_cache=True
            )

            assert result is not None
            assert result["temperature"] == 15.5
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_weather_no_cache(
        self, weather_service, mock_redis, sample_api_response
    ):
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value=sample_api_response)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await weather_service.get_current_weather(
                55.7558, 37.6173, use_cache=False
            )

            assert result is not None
            mock_redis.get.assert_not_called()


class TestWeatherServiceGetForecast:
    @pytest.mark.asyncio
    async def test_get_forecast_success(self, weather_service):
        forecast_response = {
            "list": [
                {
                    "dt": 1708156800,
                    "main": {"temp": 15, "pressure": 1013},
                    "wind": {"speed": 3.5},
                    "weather": [{"main": "Clouds"}],
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value=forecast_response)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await weather_service.get_forecast(55.7558, 37.6173, days=4)

            assert result is not None
            assert "list" in result

    @pytest.mark.asyncio
    async def test_get_forecast_api_error(self, weather_service):
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await weather_service.get_forecast(55.7558, 37.6173)

            assert result is None
