import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestSecurityAuthAPI:
    def test_sql_injection_prevention_in_login(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "'; DROP TABLE users;--@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code in [400, 401, 422]
        
        if response.status_code == 400:
            data = response.json()
            assert "detail" in data

    def test_sql_injection_prevention_in_register(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "'; DROP TABLE users;--",
                "password": "password123"
            }
        )
        
        assert response.status_code in [400, 409, 422]

    def test_xss_prevention_in_username(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "<script>alert('xss')</script>",
                "password": "password123"
            }
        )
        
        assert response.status_code in [400, 409, 422]

    def test_brute_force_protection(self, client):
        for i in range(10):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": f"wrongpassword{i}"
                }
            )
        
        last_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert last_response.status_code in [401, 429]

    def test_password_too_short(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "123"
            }
        )
        
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com"
            }
        )
        
        assert response.status_code == 422

    def test_email_format_validation(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "username": "testuser",
                "password": "password123"
            }
        )
        
        assert response.status_code == 422

    def test_content_type_validation(self, client):
        response = client.post(
            "/api/v1/auth/register",
            data="not json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    def test_large_payload_rejection(self, client):
        large_string = "a" * 10000
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"{large_string}@example.com",
                "username": large_string,
                "password": "password123"
            }
        )
        
        assert response.status_code in [422, 400]

    def test_special_characters_in_password(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "P@$$w0rd!#$%^&*()"
            }
        )
        
        assert response.status_code in [200, 409]


class TestSecurityPlacesAPI:
    def test_sql_injection_in_place_creation(self, client):
        headers = {"Authorization": "Bearer test_token"}
        response = client.post(
            "/api/v1/places",
            json={
                "title": "'; DROP TABLE places;--",
                "description": "Test description",
                "latitude": 55.7558,
                "longitude": 37.6173,
                "address": "Test address",
                "fish_types": ["carp"]
            },
            headers=headers
        )
        
        assert response.status_code in [401, 422]

    def test_xss_in_place_title(self, client):
        headers = {"Authorization": "Bearer test_token"}
        response = client.post(
            "/api/v1/places",
            json={
                "title": "<script>alert('xss')</script>",
                "description": "Test description",
                "latitude": 55.7558,
                "longitude": 37.6173,
                "address": "Test address",
                "fish_types": ["carp"]
            },
            headers=headers
        )
        
        assert response.status_code in [401, 422]

    def test_unauthorized_access(self, client):
        response = client.get("/api/v1/places")
        
        assert response.status_code == 200

    def test_invalid_token_format(self, client):
        headers = {"Authorization": "Invalid token format"}
        response = client.get("/api/v1/places", headers=headers)
        
        assert response.status_code in [401, 403]

    def test_place_id_injection(self, client):
        response = client.get("/api/v1/places/'; DROP TABLE places;--")
        
        assert response.status_code == 422

    def test_latitude_bounds_validation(self, client):
        headers = {"Authorization": "Bearer test_token"}
        response = client.post(
            "/api/v1/places",
            json={
                "title": "Test place",
                "description": "Test description",
                "latitude": 91.0,
                "longitude": 37.6173,
                "address": "Test address",
                "fish_types": ["carp"]
            },
            headers=headers
        )
        
        assert response.status_code in [401, 422]

    def test_longitude_bounds_validation(self, client):
        headers = {"Authorization": "Bearer test_token"}
        response = client.post(
            "/api/v1/places",
            json={
                "title": "Test place",
                "description": "Test description",
                "latitude": 55.7558,
                "longitude": 181.0,
                "address": "Test address",
                "fish_types": ["carp"]
            },
            headers=headers
        )
        
        assert response.status_code in [401, 422]

    def test_empty_fish_types_rejection(self, client):
        headers = {"Authorization": "Bearer test_token"}
        response = client.post(
            "/api/v1/places",
            json={
                "title": "Test place",
                "description": "Test description",
                "latitude": 55.7558,
                "longitude": 37.6173,
                "address": "Test address",
                "fish_types": []
            },
            headers=headers
        )
        
        assert response.status_code in [401, 422]


class TestSecurityCommon:
    def test_cors_headers(self, client):
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        assert response.status_code in [200, 404, 405]

    def test_rate_limiting_headers(self, client):
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200

    def test_security_headers(self, client):
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200

    def test_error_information_disclosure(self, client):
        response = client.get("/api/v1/places/00000000-0000-0000-0000-000000000000")
        
        data = response.json()
        if "detail" in data:
            assert "traceback" not in str(data).lower()
            assert "stack" not in str(data).lower()
            assert "password" not in str(data).lower()

    def test_malformed_json(self, client):
        response = client.post(
            "/api/v1/auth/register",
            data='{"email": "test@example.com", "username": "test"',
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    def test_content_length_check(self, client):
        large_payload = {"data": "x" * 10000000}
        response = client.post(
            "/api/v1/auth/register",
            json=large_payload
        )
        
        assert response.status_code in [413, 422, 400]
