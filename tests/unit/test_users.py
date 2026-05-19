import httpx
import pytest
import respx

from zendesk_mcp_ro.client import ZendeskClient
from zendesk_mcp_ro.tools.users import (
    _get_user,
    _search_users,  # noqa: F401 — used in Task 2 (search_users tests)
)

BASE = "https://test-company.zendesk.com"

USER_PAYLOAD = {
    "user": {
        "id": 101,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "role": "agent",
        "phone": "+1-555-1234",
        "time_zone": "America/Sao_Paulo",
        "locale": "pt-BR",
        "organization_id": 303,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-06-01T00:00:00Z",
        "active": True,
        "suspended": False,
        "tags": ["vip", "enterprise"],
    },
    "organizations": [
        {"id": 303, "name": "Acme Corp"},
    ],
}


@respx.mock
async def test_get_user_happy_path(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/users/101.json").mock(
        return_value=httpx.Response(200, json=USER_PAYLOAD)
    )
    result = await _get_user(zendesk_client, 101)
    assert "User #101" in result
    assert "John Doe" in result
    assert "john.doe@example.com" in result
    assert "agent" in result
    assert "+1-555-1234" in result
    assert "America/Sao_Paulo" in result
    assert "Acme Corp" in result
    assert "vip" in result
    assert "enterprise" in result


@respx.mock
async def test_get_user_no_organization(zendesk_client: ZendeskClient) -> None:
    payload = {
        "user": {
            "id": 102,
            "name": "Jane Doe",
            "email": "jane@example.com",
            "role": "end-user",
            "phone": None,
            "time_zone": "UTC",
            "locale": "en",
            "organization_id": None,
            "created_at": "2024-02-01T00:00:00Z",
            "updated_at": "2024-02-01T00:00:00Z",
            "active": True,
            "suspended": False,
            "tags": [],
        },
        "organizations": [],
    }
    respx.get(f"{BASE}/api/v2/users/102.json").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = await _get_user(zendesk_client, 102)
    assert "Jane Doe" in result
    assert "none" in result


@respx.mock
async def test_get_user_not_found(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/users/99999.json").mock(return_value=httpx.Response(404))
    result = await _get_user(zendesk_client, 99999)
    assert result == "User 99999 not found"


@respx.mock
async def test_get_user_propagates_errors(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/users/101.json").mock(return_value=httpx.Response(403))
    with pytest.raises(httpx.HTTPStatusError):
        await _get_user(zendesk_client, 101)
