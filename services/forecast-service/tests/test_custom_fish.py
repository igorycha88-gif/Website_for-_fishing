import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime

from app.endpoints.custom_fish import (
    get_custom_fish,
    add_custom_fish,
    remove_custom_fish,
    get_all_fish_types,
    MAX_CUSTOM_FISH_PER_REGION,
)
from app.models.forecast import UserAddedFish, FishType, Region


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_region():
    region = MagicMock(spec=Region)
    region.id = uuid4()
    region.name = "Москва"
    region.code = "MOW"
    region.is_active = True
    return region


@pytest.fixture
def mock_fish_type():
    fish = MagicMock(spec=FishType)
    fish.id = uuid4()
    fish.name = "Форель"
    fish.icon = "🐟"
    fish.category = "хищная"
    fish.is_active = True
    return fish


@pytest.fixture
def mock_user_id():
    return uuid4()


class TestGetCustomFish:
    @pytest.mark.asyncio
    async def test_get_custom_fish_unauthenticated(self, mock_db):
        with pytest.raises(Exception) as exc_info:
            await get_custom_fish(
                region_id=uuid4(),
                db=mock_db,
                user_id=None,
            )
        assert "401" in str(exc_info.value) or "Authentication" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_custom_fish_region_not_found(self, mock_db, mock_user_id):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(Exception) as exc_info:
            await get_custom_fish(
                region_id=uuid4(),
                db=mock_db,
                user_id=mock_user_id,
            )
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value)


class TestAddCustomFish:
    @pytest.mark.asyncio
    async def test_add_custom_fish_unauthenticated(self, mock_db):
        from app.schemas.forecast import CustomFishCreate

        with pytest.raises(Exception) as exc_info:
            await add_custom_fish(
                region_id=uuid4(),
                data=CustomFishCreate(fish_type_id=uuid4()),
                db=mock_db,
                user_id=None,
            )
        assert "401" in str(exc_info.value) or "Authentication" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_add_custom_fish_limit_exceeded(
        self, mock_db, mock_user_id, mock_region, mock_fish_type
    ):
        from app.schemas.forecast import CustomFishCreate

        mock_region_result = MagicMock()
        mock_region_result.scalar_one_or_none.return_value = mock_region

        mock_fish_result = MagicMock()
        mock_fish_result.scalar_one_or_none.return_value = mock_fish_type

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = MAX_CUSTOM_FISH_PER_REGION

        mock_db.execute.side_effect = [
            mock_region_result,
            mock_fish_result,
            mock_count_result,
        ]

        with pytest.raises(Exception) as exc_info:
            await add_custom_fish(
                region_id=mock_region.id,
                data=CustomFishCreate(fish_type_id=mock_fish_type.id),
                db=mock_db,
                user_id=mock_user_id,
            )
        assert "400" in str(exc_info.value) or "LIMIT" in str(exc_info.value).upper()


class TestRemoveCustomFish:
    @pytest.mark.asyncio
    async def test_remove_custom_fish_unauthenticated(self, mock_db):
        with pytest.raises(Exception) as exc_info:
            await remove_custom_fish(
                region_id=uuid4(),
                fish_type_id=uuid4(),
                db=mock_db,
                user_id=None,
            )
        assert "401" in str(exc_info.value) or "Authentication" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_remove_custom_fish_not_found(self, mock_db, mock_user_id):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(Exception) as exc_info:
            await remove_custom_fish(
                region_id=uuid4(),
                fish_type_id=uuid4(),
                db=mock_db,
                user_id=mock_user_id,
            )
        assert "404" in str(exc_info.value) or "NOT_FOUND" in str(exc_info.value)


class TestGetAllFishTypes:
    @pytest.mark.asyncio
    async def test_get_all_fish_types_region_not_found(self, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(Exception) as exc_info:
            await get_all_fish_types(
                region_id=uuid4(),
                db=mock_db,
                user_id=None,
            )
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value)


class TestMaxCustomFishLimit:
    def test_max_limit_is_three(self):
        assert MAX_CUSTOM_FISH_PER_REGION == 3
