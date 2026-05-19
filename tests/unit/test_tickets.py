import httpx
import pytest
import respx

from zendesk_mcp_ro.client import ZendeskClient
from zendesk_mcp_ro.tools.tickets import (
    _get_ticket,
    _get_ticket_comments,
    _get_ticket_metrics,
)

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


# ---------------------------------------------------------------------------
# get_ticket_comments
# ---------------------------------------------------------------------------

COMMENTS_PAYLOAD = {
    "comments": [
        {
            "id": 1001,
            "author_id": 101,
            "body": "Hello, I cannot log in.",
            "public": True,
            "created_at": "2024-01-10T08:00:00Z",
        },
        {
            "id": 1002,
            "author_id": 202,
            "body": "We are looking into this.",
            "public": True,
            "created_at": "2024-01-10T09:00:00Z",
        },
        {
            "id": 1003,
            "author_id": 202,
            "body": "Internal note: check auth service.",
            "public": False,
            "created_at": "2024-01-10T09:05:00Z",
        },
    ],
    "users": [
        {"id": 101, "name": "John Doe"},
        {"id": 202, "name": "Agent Smith"},
    ],
}


@respx.mock
async def test_get_ticket_comments_public_only(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/tickets/1/comments.json").mock(
        return_value=httpx.Response(200, json=COMMENTS_PAYLOAD)
    )
    result = await _get_ticket_comments(zendesk_client, 1)
    assert "John Doe" in result
    assert "Agent Smith" in result
    assert "Hello, I cannot log in." in result
    assert "We are looking into this." in result
    assert "Internal note" not in result


@respx.mock
async def test_get_ticket_comments_include_internal(
    zendesk_client: ZendeskClient,
) -> None:
    respx.get(f"{BASE}/api/v2/tickets/1/comments.json").mock(
        return_value=httpx.Response(200, json=COMMENTS_PAYLOAD)
    )
    result = await _get_ticket_comments(zendesk_client, 1, include_internal=True)
    assert "Internal note" in result
    assert "internal" in result


@respx.mock
async def test_get_ticket_comments_not_found(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/tickets/99999/comments.json").mock(
        return_value=httpx.Response(404)
    )
    result = await _get_ticket_comments(zendesk_client, 99999)
    assert result == "Ticket 99999 not found"


@respx.mock
async def test_get_ticket_comments_propagates_errors(
    zendesk_client: ZendeskClient,
) -> None:
    respx.get(f"{BASE}/api/v2/tickets/1/comments.json").mock(
        return_value=httpx.Response(403)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await _get_ticket_comments(zendesk_client, 1)


# ---------------------------------------------------------------------------
# get_ticket_metrics
# ---------------------------------------------------------------------------

METRICS_PAYLOAD = {
    "ticket_metric": {
        "ticket_id": 1,
        "reply_time_in_minutes": {"calendar": 45, "business": 30},
        "full_resolution_time_in_minutes": {"calendar": 480, "business": 240},
        "reopens": 1,
        "replies": 3,
        "assignee_updated_at": "2024-01-11T09:30:00Z",
        "requester_updated_at": "2024-01-11T08:00:00Z",
    }
}

METRICS_PAYLOAD_NO_RESOLUTION = {
    "ticket_metric": {
        "ticket_id": 2,
        "reply_time_in_minutes": {"calendar": 20, "business": 15},
        "full_resolution_time_in_minutes": None,
        "reopens": 0,
        "replies": 1,
        "assignee_updated_at": None,
        "requester_updated_at": "2024-01-10T08:05:00Z",
    }
}


@respx.mock
async def test_get_ticket_metrics_happy_path(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/tickets/1/metrics.json").mock(
        return_value=httpx.Response(200, json=METRICS_PAYLOAD)
    )
    result = await _get_ticket_metrics(zendesk_client, 1)
    assert "Ticket #1" in result
    assert "45m" in result
    assert "8h 0m" in result
    assert "Reopens: 1" in result
    assert "Replies: 3" in result


@respx.mock
async def test_get_ticket_metrics_null_resolution(
    zendesk_client: ZendeskClient,
) -> None:
    respx.get(f"{BASE}/api/v2/tickets/2/metrics.json").mock(
        return_value=httpx.Response(200, json=METRICS_PAYLOAD_NO_RESOLUTION)
    )
    result = await _get_ticket_metrics(zendesk_client, 2)
    assert "n/a" in result


@respx.mock
async def test_get_ticket_metrics_not_found(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/tickets/99999/metrics.json").mock(
        return_value=httpx.Response(404)
    )
    result = await _get_ticket_metrics(zendesk_client, 99999)
    assert result == "Ticket 99999 not found"


@respx.mock
async def test_get_ticket_metrics_propagates_errors(
    zendesk_client: ZendeskClient,
) -> None:
    respx.get(f"{BASE}/api/v2/tickets/1/metrics.json").mock(
        return_value=httpx.Response(403)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await _get_ticket_metrics(zendesk_client, 1)
