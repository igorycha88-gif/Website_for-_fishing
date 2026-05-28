import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
import uuid

from app.crud.place import PlaceCRUD
from app.schemas.place import PlaceCreate, PlaceUpdate
from app.core.constants import FORBIDDEN_WORDS


@pytest.mark.asyncio
async def test_create_place_private(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    place = await crud.create(sample_user.id, sample_place_data)
    
    assert place.id is not None
    assert place.title == sample_place_data.title
    assert place.owner_id == sample_user.id
    assert place.is_public is False
    assert place.status == "active"


@pytest.mark.asyncio
async def test_create_place_public_requires_moderation(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    public_place_data = sample_place_data.model_copy()
    public_place_data.is_public = True
    
    place = await crud.create(str(sample_user.id), public_place_data)
    
    assert place.is_public is True
    assert place.status == "pending_moderation"


@pytest.mark.asyncio
async def test_create_place_validation_min_fish_types(db_session: AsyncSession, sample_user):
    crud = PlaceCRUD(db_session)
    
    place_data = PlaceCreate(
        title="Тест",
        description="Описание",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
        address="Москва, Россия",
        fish_types=[],
        is_public=False
    )
    
    with pytest.raises(ValueError, match="At least one fish type"):
        await crud.create(str(sample_user.id), place_data)


@pytest.mark.asyncio
async def test_create_place_public_requires_images(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    public_place_data = sample_place_data.model_copy()
    public_place_data.is_public = True
    public_place_data.images = []
    
    with pytest.raises(ValueError, match="Public places must have at least one image"):
        await crud.create(str(sample_user.id), public_place_data)


@pytest.mark.asyncio
async def test_create_place_forbidden_words_title(db_session: AsyncSession, sample_user):
    crud = PlaceCRUD(db_session)
    
    forbidden_word = FORBIDDEN_WORDS[0]
    place_data = PlaceCreate(
        title=f"Место с {forbidden_word} словом",
        description="Описание",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
        address="Москва, Россия",
        fish_types=["carp"],
        is_public=False
    )
    
    with pytest.raises(ValueError, match="forbidden words"):
        await crud.create(str(sample_user.id), place_data)


@pytest.mark.asyncio
async def test_get_by_id(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    created = await crud.create(str(sample_user.id), sample_place_data)
    found = await crud.get_by_id(str(created.id))
    
    assert found is not None
    assert found.id == created.id
    assert found.title == created.title


@pytest.mark.asyncio
async def test_get_by_id_not_found(db_session: AsyncSession):
    crud = PlaceCRUD(db_session)
    
    fake_id = str(uuid.uuid4())
    found = await crud.get_by_id(fake_id)
    
    assert found is None


@pytest.mark.asyncio
async def test_get_many(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    await crud.create(str(sample_user.id), sample_place_data)
    
    places, total = await crud.get_many(page=1, limit=10)
    
    assert len(places) == 1
    assert total == 1
    assert places[0].title == sample_place_data.title


@pytest.mark.asyncio
async def test_get_many_filter_by_owner(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    await crud.create(str(sample_user.id), sample_place_data)
    
    places, total = await crud.get_many(owner_id=str(sample_user.id))
    
    assert len(places) == 1
    assert total == 1


@pytest.mark.asyncio
async def test_get_many_filter_by_status(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    place_data = sample_place_data.model_copy()
    place_data.is_public = True
    await crud.create(str(sample_user.id), place_data)
    
    places, total = await crud.get_many(status="pending_moderation")
    
    assert len(places) == 1
    assert total == 1
    assert places[0].status == "pending_moderation"


@pytest.mark.asyncio
async def test_get_many_filter_by_fish_types(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    await crud.create(str(sample_user.id), sample_place_data)
    
    places, total = await crud.get_many(fish_types=["carp"])
    
    assert len(places) == 1
    assert total == 1


@pytest.mark.asyncio
async def test_get_many_filter_by_min_rating(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    place_data = sample_place_data.model_copy()
    place_data.rating_avg = Decimal("4.5")
    await crud.create(str(sample_user.id), place_data)
    
    places, total = await crud.get_many(min_rating=4.0)
    
    assert len(places) == 1
    assert total == 1


@pytest.mark.asyncio
async def test_get_many_pagination(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    for i in range(5):
        place_data = sample_place_data.model_copy()
        place_data.title = f"Место {i+1}"
        await crud.create(str(sample_user.id), place_data)
    
    places, total = await crud.get_many(page=1, limit=2)
    
    assert len(places) == 2
    assert total == 5
    assert places[0].title == "Место 5"


@pytest.mark.asyncio
async def test_update_place(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    created = await crud.create(str(sample_user.id), sample_place_data)
    
    update_data = PlaceUpdate(title="Обновленное название")
    updated = await crud.update(str(created.id), update_data)
    
    assert updated is not None
    assert updated.title == "Обновленное название"
    assert updated.description == sample_place_data.description


@pytest.mark.asyncio
async def test_update_place_not_found(db_session: AsyncSession):
    crud = PlaceCRUD(db_session)
    
    fake_id = str(uuid.uuid4())
    update_data = PlaceUpdate(title="Новое название")
    
    updated = await crud.update(fake_id, update_data)
    
    assert updated is None


@pytest.mark.asyncio
async def test_delete_place(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    created = await crud.create(str(sample_user.id), sample_place_data)
    
    deleted = await crud.delete(str(created.id))
    
    assert deleted is True
    
    found = await crud.get_by_id(str(created.id))
    assert found is None


@pytest.mark.asyncio
async def test_delete_place_not_found(db_session: AsyncSession):
    crud = PlaceCRUD(db_session)
    
    fake_id = str(uuid.uuid4())
    deleted = await crud.delete(fake_id)
    
    assert deleted is False


@pytest.mark.asyncio
async def test_get_nearby(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    await crud.create(str(sample_user.id), sample_place_data)
    
    nearby = await crud.get_nearby(55.7558, 37.6173, radius=50)
    
    assert len(nearby) == 1
    assert nearby[0].title == sample_place_data.title


@pytest.mark.asyncio
async def test_moderate_approve(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    place_data = sample_place_data.model_copy()
    place_data.is_public = True
    created = await crud.create(str(sample_user.id), place_data)
    
    moderated = await crud.moderate(str(created.id), "approve")
    
    assert moderated is not None
    assert moderated.status == "active"


@pytest.mark.asyncio
async def test_moderate_reject(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    place_data = sample_place_data.model_copy()
    place_data.is_public = True
    created = await crud.create(str(sample_user.id), place_data)
    
    moderated = await crud.moderate(str(created.id), "reject", "Spam place")
    
    assert moderated is not None
    assert moderated.status == "rejected"


@pytest.mark.asyncio
async def test_get_statistics(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    created = await crud.create(str(sample_user.id), sample_place_data)
    
    stats = await crud.get_statistics(str(created.id))
    
    assert stats is not None
    assert stats["reports_count"] == 0
    assert stats["avg_rating"] == 0.0


@pytest.mark.asyncio
async def test_get_by_owner(db_session: AsyncSession, sample_user, sample_place_data):
    crud = PlaceCRUD(db_session)
    
    await crud.create(str(sample_user.id), sample_place_data)
    
    places, total = await crud.get_by_owner(str(sample_user.id))
    
    assert len(places) == 1
    assert total == 1
