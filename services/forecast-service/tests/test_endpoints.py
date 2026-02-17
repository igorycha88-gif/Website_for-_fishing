import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from decimal import Decimal

from app.models.forecast import Region


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
