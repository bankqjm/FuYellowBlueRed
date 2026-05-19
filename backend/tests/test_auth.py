import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuth:
    async def test_register(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/register", json={
            "phone": "13900000001",
            "password": "Test123456",
            "confirm_password": "Test123456",
            "role": "USER"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "id" in data["data"]
        assert data["data"]["phone"] == "13900000001"

    async def test_login(self, client: AsyncClient, test_user):
        response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "Test123456"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "access_token" in data["data"]

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        response = await client.post("/api/v1/auth/login", json={
            "phone": "13800138000",
            "password": "WrongPassword"
        })
        assert response.status_code == 400

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/login", json={
            "phone": "13999999999",
            "password": "Test123456"
        })
        assert response.status_code == 400

    async def test_get_current_user(self, client: AsyncClient, user_token, test_user):
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["phone"] == "13800138000"
