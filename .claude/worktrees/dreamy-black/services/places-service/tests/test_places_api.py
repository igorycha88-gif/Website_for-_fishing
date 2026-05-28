import pytest
from decimal import Decimal
from fastapi import status

from app.models.place import Place
from app.models.user import User
from app.schemas.place import PlaceCreate, PlaceUpdate


@pytest.mark.asyncio
async def test_create_place_success(client, sample_place_data, auth_headers):
    response = await client.post(
        "/api/v1/places",
        json=sample_place_data.model_dump(),
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == sample_place_data.title
    assert data["description"] == sample_place_data.description
    assert data["owner_id"] is not None
    assert data["status"] == "active"
    assert data["is_public"] is False


@pytest.mark.asyncio
async def test_create_place_unauthorized(client, sample_place_data):
    response = await client.post(
        "/api/v1/places",
        json=sample_place_data.model_dump()
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_create_place_public_pending_moderation(client, sample_place_data, auth_headers):
    place_data = sample_place_data.model_copy()
    place_data.is_public = True
    place_data.images = ["https://example.com/image.jpg"]
    
    response = await client.post(
        "/api/v1/places",
        json=place_data.model_dump(),
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["is_public"] is True
    assert data["status"] == "pending_moderation"


@pytest.mark.asyncio
async def test_create_place_public_no_images(client, sample_place_data, auth_headers):
    place_data = sample_place_data.model_copy()
    place_data.is_public = True
    place_data.images = []
    
    response = await client.post(
        "/api/v1/places",
        json=place_data.model_dump(),
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_create_place_no_fish_types(client, sample_place_data, auth_headers):
    place_data = sample_place_data.model_copy()
    place_data.fish_types = []
    
    response = await client.post(
        "/api/v1/places",
        json=place_data.model_dump(),
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_places(client, db_session, sample_user, sample_place_data, auth_headers):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    await crud.create(str(sample_user.id), sample_place_data)
    
    response = await client.get("/api/v1/places")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_get_places_filter_by_owner(client, db_session, sample_user, sample_place_data, auth_headers):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    await crud.create(str(sample_user.id), sample_place_data)
    
    response = await client.get(
        f"/api/v1/places?owner_id={sample_user.id}",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_places_filter_by_status(client, db_session, sample_user, sample_place_data):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    
    place_data = sample_place_data.model_copy()
    place_data.is_public = True
    place_data.images = ["https://example.com/image.jpg"]
    await crud.create(str(sample_user.id), place_data)
    
    response = await client.get("/api/v1/places?status=pending_moderation")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "pending_moderation"


@pytest.mark.asyncio
async def test_get_places_filter_by_fish_types(client, db_session, sample_user, sample_place_data):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    await crud.create(str(sample_user.id), sample_place_data)
    
    response = await client.get("/api/v1/places?fish_types=carp,bream")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_places_filter_by_min_rating(client, db_session, sample_user, sample_place_data):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    
    place_data = sample_place_data.model_copy()
    place_data.rating_avg = Decimal("4.5")
    await crud.create(str(sample_user.id), place_data)
    
    response = await client.get("/api/v1/places?min_rating=4.0")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_places_pagination(client, db_session, sample_user, sample_place_data):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    
    for i in range(5):
        place_data = sample_place_data.model_copy()
        place_data.title = f"Место {i+1}"
        await crud.create(str(sample_user.id), place_data)
    
    response = await client.get("/api/v1/places?page=1&limit=2")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["pages"] == 3


@pytest.mark.asyncio
async def test_get_place_by_id(client, db_session, sample_user, sample_place_data):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    created = await crud.create(str(sample_user.id), sample_place_data)
    
    response = await client.get(f"/api/v1/places/{created.id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(created.id)
    assert data["title"] == sample_place_data.title


@pytest.mark.asyncio
async def test_get_place_not_found(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    response = await client.get(f"/api/v1/places/{fake_id}")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_place_success(client, db_session, sample_user, sample_place_data, auth_headers):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    created = await crud.create(str(sample_user.id), sample_place_data)
    
    update_data = {"title": "Обновленное название"}
    
    response = await client.put(
        f"/api/v1/places/{created.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Обновленное название"


@pytest.mark.asyncio
async def test_update_place_not_owner(client, db_session, sample_user, sample_place_data, auth_headers):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    created = await crud.create(str(sample_user.id), sample_place_data)
    
    update_data = {"title": "Взломанное название"}
    wrong_headers = {"Authorization": "Bearer wrong_token"}
    
    response = await client.put(
        f"/api/v1/places/{created.id}",
        json=update_data,
        headers=wrong_headers
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_update_place_not_found(client, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    update_data = {"title": "Новое название"}
    
    response = await client.put(
        f"/api/v1/places/{fake_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_place_success(client, db_session, sample_user, sample_place_data, auth_headers):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    created = await crud.create(str(sample_user.id), sample_place_data)
    
    response = await client.delete(
        f"/api/v1/places/{created.id}",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    get_response = await client.get(f"/api/v1/places/{created.id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_place_not_owner(client, db_session, sample_user, sample_place_data, auth_headers):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    created = await crud.create(str(sample_user.id), sample_place_data)
    
    wrong_headers = {"Authorization": "Bearer wrong_token"}
    
    response = await client.delete(
        f"/api/v1/places/{created.id}",
        headers=wrong_headers
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_delete_place_not_found(client, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    response = await client.delete(
        f"/api/v1/places/{fake_id}",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_nearby_places(client, db_session, sample_user, sample_place_data):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    await crud.create(str(sample_user.id), sample_place_data)
    
    response = await client.get("/api/v1/places/nearby?lat=55.7558&lng=37.6173&radius=50")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_fish_types(client):
    response = await client.get("/api/v1/places/fish-types")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 30
    assert data[0]["id"] == "carp"
    assert data[0]["name"] == "Карась"


@pytest.mark.asyncio
async def test_get_facilities(client):
    response = await client.get("/api/v1/places/facilities")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 15
    assert data[0]["id"] == "parking"
    assert data[0]["name"] == "Парковка"


@pytest.mark.asyncio
async def test_moderate_place_approve(client, db_session, sample_user, sample_place_data, auth_headers):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    
    place_data = sample_place_data.model_copy()
    place_data.is_public = True
    place_data.images = ["https://example.com/image.jpg"]
    created = await crud.create(str(sample_user.id), place_data)
    
    moderation_data = {"action": "approve"}
    
    response = await client.post(
        f"/api/v1/places/{created.id}/moderate",
        json=moderation_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_moderate_place_reject(client, db_session, sample_user, sample_place_data, auth_headers):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    
    place_data = sample_place_data.model_copy()
    place_data.is_public = True
    place_data.images = ["https://example.com/image.jpg"]
    created = await crud.create(str(sample_user.id), place_data)
    
    moderation_data = {"action": "reject", "reason": "Spam"}
    
    response = await client.post(
        f"/api/v1/places/{created.id}/moderate",
        json=moderation_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "rejected"


@pytest.mark.asyncio
async def test_moderate_place_non_admin(client, db_session, sample_user, sample_place_data):
    from app.crud.place import PlaceCRUD
    from app.core.security import create_access_token
    crud = PlaceCRUD(db_session)
    
    place_data = sample_place_data.model_copy()
    place_data.is_public = True
    place_data.images = ["https://example.com/image.jpg"]
    created = await crud.create(str(sample_user.id), place_data)
    
    non_admin_user = User(
        email="user@example.com",
        username="nonadmin",
        password_hash="hash",
        role="user",
        is_verified=True
    )
    db_session.add(non_admin_user)
    await db_session.commit()
    
    token = create_access_token(data={"sub": str(non_admin_user.id)})
    user_headers = {"Authorization": f"Bearer {token}"}
    
    moderation_data = {"action": "approve"}
    
    response = await client.post(
        f"/api/v1/places/{created.id}/moderate",
        json=moderation_data,
        headers=user_headers
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_get_place_statistics(client, db_session, sample_user, sample_place_data):
    from app.crud.place import PlaceCRUD
    crud = PlaceCRUD(db_session)
    created = await crud.create(str(sample_user.id), sample_place_data)
    
    response = await client.get(f"/api/v1/places/{created.id}/statistics")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "reports_count" in data
    assert "avg_rating" in data
    assert "top_fish" in data
    assert "seasonality" in data


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/v1/health")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "places-service"


@pytest.mark.asyncio
async def test_get_places_invalid_bbox(client):
    response = await client.get("/api/v1/places?bbox=invalid,format")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
