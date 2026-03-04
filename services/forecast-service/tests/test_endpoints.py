import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from decimal import Decimal
from datetime import date

from app.models.forecast import Region, WeatherData


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def sample_region():
    return Region(
        id=uuid4(),
        name="Москва",
        code="MOW",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
        timezone="Europe/Moscow",
        is_active=True,
    )


@pytest.fixture
def sample_weather_data(sample_region):
    return WeatherData(
        id=uuid4(),
        region_id=sample_region.id,
        forecast_date=date.today(),
        forecast_hour=12,
        temperature=Decimal("-3.5"),
        pressure_hpa=1013,
        wind_speed=Decimal("3.5"),
        weather_icon="01d",
    )


class TestRegionsEndpoint:
    @pytest.mark.asyncio
    async def test_get_regions_list(self, mock_db, sample_region):
        from app.endpoints.regions import get_regions

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_region]
        mock_result.scalars.return_value = mock_scalars

        with patch("app.endpoints.regions.select") as mock_select:
            mock_db.execute.return_value = mock_result

            result = await get_regions(is_active=True, db=mock_db)

            assert result.total == 1
            assert len(result.regions) == 1
            assert result.regions[0].name == "Москва"

    @pytest.mark.asyncio
    async def test_get_region_by_id_success(self, mock_db, sample_region):
        from app.endpoints.regions import get_region
        from fastapi import HTTPException

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_region

        with patch("app.endpoints.regions.select") as mock_select:
            mock_db.execute.return_value = mock_result

            result = await get_region(region_id=sample_region.id, db=mock_db)

            assert result.name == "Москва"
            assert result.code == "MOW"

    @pytest.mark.asyncio
    async def test_get_region_by_id_not_found(self, mock_db):
        from app.endpoints.regions import get_region
        from fastapi import HTTPException

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        with patch("app.endpoints.regions.select") as mock_select:
            mock_db.execute.return_value = mock_result

            with pytest.raises(HTTPException) as exc_info:
                await get_region(region_id=uuid4(), db=mock_db)

            assert exc_info.value.status_code == 404


class TestAvailableDatesEndpoint:
    @pytest.mark.asyncio
    async def test_get_available_dates_success(self, mock_db, sample_region):
        from app.endpoints.forecast import get_available_dates

        dates = [date.today(), date.today()]
        mock_result = MagicMock()
        mock_result.all.return_value = [(dates[0],), (dates[1],)]
        mock_db.execute.return_value = mock_result

        result = await get_available_dates(region_id=sample_region.id, db=mock_db)

        assert result.region_id == sample_region.id
        assert len(result.dates) == 2
        assert str(dates[0]) in result.dates

    @pytest.mark.asyncio
    async def test_get_available_dates_empty(self, mock_db, sample_region):
        from app.endpoints.forecast import get_available_dates

        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await get_available_dates(region_id=sample_region.id, db=mock_db)

        assert result.region_id == sample_region.id
        assert len(result.dates) == 0


class TestDaySummaryEndpoint:
    @pytest.mark.asyncio
    async def test_get_day_summary_success(
        self, mock_db, sample_region, sample_weather_data
    ):
        from app.endpoints.forecast import get_day_summary

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_weather_data
        mock_db.execute.return_value = mock_result

        result = await get_day_summary(
            region_id=sample_region.id, forecast_date=date.today(), db=mock_db
        )

        assert result.date == str(date.today())
        assert result.temperature == float(sample_weather_data.temperature)
        assert result.weather_icon == sample_weather_data.weather_icon
        assert result.wind_speed == float(sample_weather_data.wind_speed)

    @pytest.mark.asyncio
    async def test_get_day_summary_not_found(self, mock_db, sample_region):
        from app.endpoints.forecast import get_day_summary
        from fastapi import HTTPException

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_day_summary(
                region_id=sample_region.id, forecast_date=date.today(), db=mock_db
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Day not found"

    @pytest.mark.asyncio
    async def test_get_day_summary_null_values(self, mock_db, sample_region):
        from app.endpoints.forecast import get_day_summary

        weather_data = WeatherData(
            id=uuid4(),
            region_id=sample_region.id,
            forecast_date=date.today(),
            forecast_hour=12,
            temperature=None,
            pressure_hpa=None,
            wind_speed=None,
            weather_icon=None,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = weather_data
        mock_db.execute.return_value = mock_result

        result = await get_day_summary(
            region_id=sample_region.id, forecast_date=date.today(), db=mock_db
        )

        assert result.temperature is None
        assert result.weather_icon is None
        assert result.wind_speed is None
