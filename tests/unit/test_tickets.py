import httpx
import pytest
import respx

from zendesk_mcp_ro.client import ZendeskClient
from zendesk_mcp_ro.tools.tickets import _get_ticket

BASE = "https://test-company.zendesk.com"

TICKET_PAYLOAD = {
    "ticket": {
        "id": 1,
        "subject": "Login not working",
        "status": "open",
        "priority": "high",
        "type": "problem",
        "requester_id": 101,
        "assignee_id": 202,
        "organization_id": 303,
        "tags": ["billing", "urgent"],
        "created_at": "2024-01-10T08:00:00Z",
        "updated_at": "2024-01-11T09:30:00Z",
        "description": "User cannot log in since yesterday.",
        "via": {"channel": "email"},
        "group_id": 404,
        "satisfaction_rating": {"score": "good"},
    },
    "users": [
        {"id": 101, "name": "John Doe"},
        {"id": 202, "name": "Agent Smith"},
    ],
    "organizations": [
        {"id": 303, "name": "Acme Corp"},
    ],
    "groups": [
        {"id": 404, "name": "Support Tier 1"},
    ],
}


@respx.mock
async def test_get_ticket_happy_path(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/tickets/1.json").mock(
        return_value=httpx.Response(200, json=TICKET_PAYLOAD)
    )
    result = await _get_ticket(zendesk_client, 1)
    assert "Ticket #1" in result
    assert "Login not working" in result
    assert "open" in result
    assert "high" in result
    assert "problem" in result
    assert "email" in result
    assert "good" in result
    assert "billing" in result
    assert "User cannot log in" in result
    assert "John Doe" in result
    assert "Agent Smith" in result
    assert "Acme Corp" in result
    assert "Support Tier 1" in result


@respx.mock
async def test_get_ticket_unassigned(zendesk_client: ZendeskClient) -> None:
    payload = {
        "ticket": {
            "id": 2,
            "subject": "No assignee ticket",
            "status": "new",
            "priority": "normal",
            "type": None,
            "requester_id": 101,
            "assignee_id": None,
            "organization_id": None,
            "tags": [],
            "created_at": "2024-01-10T08:00:00Z",
            "updated_at": "2024-01-10T08:00:00Z",
            "description": "Waiting for triage.",
            "via": {"channel": "api"},
            "group_id": None,
            "satisfaction_rating": None,
        },
        "users": [{"id": 101, "name": "John Doe"}],
        "organizations": [],
        "groups": [],
    }
    respx.get(f"{BASE}/api/v2/tickets/2.json").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = await _get_ticket(zendesk_client, 2)
    assert "Unassigned" in result


@respx.mock
async def test_get_ticket_not_found(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/tickets/99999.json").mock(
        return_value=httpx.Response(404)
    )
    result = await _get_ticket(zendesk_client, 99999)
    assert result == "Ticket 99999 not found"


@respx.mock
async def test_get_ticket_propagates_other_errors(
    zendesk_client: ZendeskClient,
) -> None:
    respx.get(f"{BASE}/api/v2/tickets/1.json").mock(return_value=httpx.Response(403))
    with pytest.raises(httpx.HTTPStatusError):
        await _get_ticket(zendesk_client, 1)
