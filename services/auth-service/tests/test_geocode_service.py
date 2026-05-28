import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.geocode import GeocodeService


@pytest.fixture
def mock_redis():
    return AsyncMock()


@pytest.fixture
def geocode_service(mock_redis):
    return GeocodeService(redis_client=mock_redis)


@pytest.mark.asyncio
async def test_get_city_coordinates_from_cache(geocode_service, mock_redis):
    city = "Москва"
    expected_coords = {"lat": 55.7558, "lon": 37.6173}

    mock_redis.get.return_value = b'{"lat": 55.7558, "lon": 37.6173}'

    result = await geocode_service.get_city_coordinates(city)

    assert result == expected_coords
    mock_redis.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_city_coordinates_empty_string(geocode_service):
    result = await geocode_service.get_city_coordinates("")

    assert result is None


@pytest.mark.asyncio
async def test_get_city_coordinates_whitespace_only(geocode_service):
    result = await geocode_service.get_city_coordinates("   ")

    assert result is None


@pytest.mark.asyncio
async def test_get_city_coordinates_from_api(geocode_service, mock_redis):
    city = "Санкт-Петербург"
    expected_coords = {"lat": 59.9343, "lon": 30.3351}

    mock_redis.get.return_value = None
    mock_redis.setex.return_value = None

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(
        return_value={
            "response": {
                "GeoObjectCollection": {
                    "featureMember": [
                        {"GeoObject": {"Point": {"pos": "30.3351 59.9343"}}}
                    ]
                }
            }
        }
    )

    with patch("httpx.AsyncClient") as mock_httpx:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_httpx.return_value.__aenter__.return_value = mock_client

        result = await geocode_service.get_city_coordinates(city)

        assert result == expected_coords
        mock_redis.get.assert_called_once()
        mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_get_city_coordinates_api_returns_empty(geocode_service, mock_redis):
    city = "НеизвестныйГород"
    expected_fallback = {"lat": 55.7558, "lon": 37.6173}

    mock_redis.get.return_value = None

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(
        return_value={"response": {"GeoObjectCollection": {"featureMember": []}}}
    )

    with patch("httpx.AsyncClient") as mock_httpx:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_httpx.return_value.__aenter__.return_value = mock_client

        result = await geocode_service.get_city_coordinates(city)

        assert result == expected_fallback
        mock_redis.get.assert_called_once()
        mock_redis.setex.assert_not_called()


@pytest.mark.asyncio
async def test_get_city_coordinates_api_error(geocode_service, mock_redis):
    city = "Москва"
    expected_fallback = {"lat": 55.7558, "lon": 37.6173}

    mock_redis.get.return_value = None

    with patch("httpx.AsyncClient") as mock_httpx:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("API Error"))
        mock_httpx.return_value.__aenter__.return_value = mock_client

        result = await geocode_service.get_city_coordinates(city)

        assert result == expected_fallback


@pytest.mark.asyncio
async def test_get_city_coordinates_malformed_api_response(geocode_service, mock_redis):
    city = "Москва"
    expected_fallback = {"lat": 55.7558, "lon": 37.6173}

    mock_redis.get.return_value = None

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(
        return_value={
            "response": {
                "GeoObjectCollection": {"featureMember": [{"GeoObject": {"Point": {}}}]}
            }
        }
    )

    with patch("httpx.AsyncClient") as mock_httpx:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_httpx.return_value.__aenter__.return_value = mock_client

        result = await geocode_service.get_city_coordinates(city)

        assert result == expected_fallback
        mock_redis.get.assert_called_once()
        mock_redis.setex.assert_not_called()


@pytest.mark.asyncio
async def test_get_city_coordinates_cache_save_error(geocode_service, mock_redis):
    city = "Москва"
    expected_coords = {"lat": 55.7558, "lon": 37.6173}

    mock_redis.get.return_value = None
    mock_redis.setex.side_effect = Exception("Redis Error")

    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "response": {
            "GeoObjectCollection": {
                "featureMember": [{"GeoObject": {"Point": {"pos": "37.6173 55.7558"}}}]
            }
        }
    }

    with patch("httpx.AsyncClient") as mock_httpx:
        mock_httpx.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await geocode_service.get_city_coordinates(city)

        assert result == expected_coords


@pytest.mark.asyncio
async def test_get_city_coordinates_no_redis_client():
    service = GeocodeService(redis_client=None)
    city = "Москва"
    expected_coords = {"lat": 55.7558, "lon": 37.6173}

    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "response": {
            "GeoObjectCollection": {
                "featureMember": [{"GeoObject": {"Point": {"pos": "37.6173 55.7558"}}}]
            }
        }
    }

    with patch("httpx.AsyncClient") as mock_httpx:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_httpx.return_value.__aenter__.return_value = mock_client

        result = await service.get_city_coordinates(city)

        assert result == expected_coords


@pytest.mark.asyncio
async def test_get_city_coordinates_malformed_json_cache(geocode_service, mock_redis):
    city = "Москва"

    mock_redis.get.return_value = b"invalid json"

    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "response": {
            "GeoObjectCollection": {
                "featureMember": [{"GeoObject": {"Point": {"pos": "37.6173 55.7558"}}}]
            }
        }
    }

    with patch("httpx.AsyncClient") as mock_httpx:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_httpx.return_value.__aenter__.return_value = mock_client

        result = await geocode_service.get_city_coordinates(city)

        assert result == {"lat": 55.7558, "lon": 37.6173}


@pytest.mark.asyncio
async def test_get_default_coordinates(geocode_service):
    result = await geocode_service.get_default_coordinates()

    assert result == {"lat": 55.7558, "lon": 37.6173}


@pytest.mark.asyncio
async def test_check_redis_connection_success(geocode_service, mock_redis):
    mock_redis.ping.return_value = True

    result = await geocode_service.check_redis_connection()

    assert result is True
    mock_redis.ping.assert_called_once()


@pytest.mark.asyncio
async def test_check_redis_connection_failure(geocode_service, mock_redis):
    mock_redis.ping.side_effect = Exception("Connection error")

    result = await geocode_service.check_redis_connection()

    assert result is False


@pytest.mark.asyncio
async def test_check_redis_connection_no_client():
    service = GeocodeService(redis_client=None)

    result = await service.check_redis_connection()

    assert result is False


@pytest.mark.asyncio
async def test_get_city_coordinates_exception_handling(geocode_service, mock_redis):
    city = "Москва"

    mock_redis.get.side_effect = Exception("Redis connection error")

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(
        return_value={
            "response": {
                "GeoObjectCollection": {
                    "featureMember": [
                        {"GeoObject": {"Point": {"pos": "37.617698 55.755864"}}}
                    ]
                }
            }
        }
    )

    with patch("httpx.AsyncClient") as mock_httpx:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_httpx.return_value.__aenter__.return_value = mock_client

        result = await geocode_service.get_city_coordinates(city)

        assert result == {"lat": 55.755864, "lon": 37.617698}
