import httpx
import pytest
import respx

from zendesk_mcp_ro.client import ZendeskClient
from zendesk_mcp_ro.tools.tickets import (
    _get_linked_incidents,
    _get_ticket,
    _get_ticket_audits,
    _get_ticket_comments,
    _get_ticket_metrics,
    _get_tickets_count_by_status,
    _list_tickets,
    _search_tickets,
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


# ---------------------------------------------------------------------------
# search_tickets
# ---------------------------------------------------------------------------

SEARCH_PAYLOAD = {
    "results": [
        {
            "id": 10,
            "subject": "Billing error on invoice",
            "status": "open",
            "priority": "high",
            "requester_id": 101,
            "assignee_id": 202,
            "updated_at": "2024-01-11T09:30:00Z",
        },
        {
            "id": 11,
            "subject": "Cannot access portal",
            "status": "pending",
            "priority": "normal",
            "requester_id": 101,
            "assignee_id": None,
            "updated_at": "2024-01-10T08:00:00Z",
        },
    ],
    "count": 42,
    "users": [
        {"id": 101, "name": "John Doe"},
        {"id": 202, "name": "Agent Smith"},
    ],
}


@respx.mock
async def test_search_tickets_returns_list(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/search.json").mock(
        return_value=httpx.Response(200, json=SEARCH_PAYLOAD)
    )
    result = await _search_tickets(zendesk_client, "billing")
    assert "Showing 2 of 42" in result
    assert "#10" in result
    assert "Billing error on invoice" in result
    assert "open" in result
    assert "high" in result
    assert "Agent Smith" in result
    assert "#11" in result
    assert "Cannot access portal" in result
    assert "Unassigned" in result


@respx.mock
async def test_search_tickets_empty_result(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/search.json").mock(
        return_value=httpx.Response(200, json={"results": [], "count": 0, "users": []})
    )
    result = await _search_tickets(zendesk_client, "xyznotfound")
    assert result == "No tickets found for query: xyznotfound"


@respx.mock
async def test_search_tickets_propagates_errors(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/search.json").mock(return_value=httpx.Response(403))
    with pytest.raises(httpx.HTTPStatusError):
        await _search_tickets(zendesk_client, "billing")


# ---------------------------------------------------------------------------
# list_tickets
# ---------------------------------------------------------------------------

LIST_PAYLOAD = {
    "results": [
        {
            "id": 20,
            "subject": "Password reset request",
            "status": "open",
            "priority": "normal",
            "requester_id": 101,
            "assignee_id": 202,
            "updated_at": "2024-01-12T10:00:00Z",
        },
    ],
    "count": 1,
    "users": [
        {"id": 101, "name": "John Doe"},
        {"id": 202, "name": "Agent Smith"},
    ],
}


@respx.mock
async def test_list_tickets_with_status(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/search.json").mock(
        return_value=httpx.Response(200, json=LIST_PAYLOAD)
    )
    result = await _list_tickets(zendesk_client, status="open")
    assert "Showing 1 of 1" in result
    assert "#20" in result
    assert "Password reset request" in result
    assert "Agent Smith" in result


@respx.mock
async def test_list_tickets_without_status(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/search.json").mock(
        return_value=httpx.Response(200, json=LIST_PAYLOAD)
    )
    result = await _list_tickets(zendesk_client)
    assert "#20" in result


@respx.mock
async def test_list_tickets_empty(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/search.json").mock(
        return_value=httpx.Response(200, json={"results": [], "count": 0, "users": []})
    )
    result = await _list_tickets(zendesk_client, status="solved")
    assert result == "No tickets found."


@respx.mock
async def test_list_tickets_propagates_errors(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/search.json").mock(return_value=httpx.Response(403))
    with pytest.raises(httpx.HTTPStatusError):
        await _list_tickets(zendesk_client, status="open")


# ---------------------------------------------------------------------------
# get_ticket_audits
# ---------------------------------------------------------------------------

AUDITS_PAYLOAD = {
    "audits": [
        {
            "id": 1001,
            "ticket_id": 1,
            "created_at": "2024-01-10T08:00:00Z",
            "author_id": 101,
            "events": [
                {"id": 2001, "type": "Create"},
                {
                    "id": 2002,
                    "type": "Change",
                    "field_name": "status",
                    "previous_value": None,
                    "value": "new",
                },
            ],
        },
        {
            "id": 1002,
            "ticket_id": 1,
            "created_at": "2024-01-10T09:00:00Z",
            "author_id": 202,
            "events": [
                {
                    "id": 2003,
                    "type": "Change",
                    "field_name": "assignee_id",
                    "previous_value": None,
                    "value": "202",
                },
                {
                    "id": 2004,
                    "type": "Change",
                    "field_name": "status",
                    "previous_value": "new",
                    "value": "open",
                },
            ],
        },
        {
            "id": 1003,
            "ticket_id": 1,
            "created_at": "2024-01-11T09:30:00Z",
            "author_id": 202,
            "events": [
                {
                    "id": 2005,
                    "type": "Change",
                    "field_name": "status",
                    "previous_value": "open",
                    "value": "solved",
                },
            ],
        },
    ],
    "users": [
        {"id": 101, "name": "John Doe"},
        {"id": 202, "name": "Agent Smith"},
    ],
}


@respx.mock
async def test_get_ticket_audits_happy_path(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/tickets/1/audits.json").mock(
        return_value=httpx.Response(200, json=AUDITS_PAYLOAD)
    )
    result = await _get_ticket_audits(zendesk_client, 1)
    assert "Ticket #1" in result
    assert "John Doe" in result
    assert "Agent Smith" in result
    assert "2024-01-10T08:00:00Z" in result
    assert "Ticket created" in result
    assert "status" in result
    assert "new → open" in result
    assert "open → solved" in result
    assert "assignee_id" in result


@respx.mock
async def test_get_ticket_audits_empty(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/tickets/1/audits.json").mock(
        return_value=httpx.Response(200, json={"audits": [], "users": []})
    )
    result = await _get_ticket_audits(zendesk_client, 1)
    assert result == "No audit trail found for ticket #1."


@respx.mock
async def test_get_ticket_audits_not_found(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/tickets/99999/audits.json").mock(
        return_value=httpx.Response(404)
    )
    result = await _get_ticket_audits(zendesk_client, 99999)
    assert result == "Ticket 99999 not found"


@respx.mock
async def test_get_ticket_audits_propagates_errors(
    zendesk_client: ZendeskClient,
) -> None:
    respx.get(f"{BASE}/api/v2/tickets/1/audits.json").mock(
        return_value=httpx.Response(403)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await _get_ticket_audits(zendesk_client, 1)


# ---------------------------------------------------------------------------
# get_linked_incidents
# ---------------------------------------------------------------------------

INCIDENTS_PAYLOAD = {
    "tickets": [
        {
            "id": 50,
            "subject": "Cannot login",
            "status": "open",
            "priority": "high",
            "requester_id": 101,
            "assignee_id": 202,
            "updated_at": "2024-01-11T09:30:00Z",
        },
        {
            "id": 51,
            "subject": "App crash on startup",
            "status": "pending",
            "priority": "normal",
            "requester_id": 103,
            "assignee_id": None,
            "updated_at": "2024-01-10T08:00:00Z",
        },
    ],
    "users": [
        {"id": 101, "name": "John Doe"},
        {"id": 202, "name": "Agent Smith"},
        {"id": 103, "name": "Jane Doe"},
    ],
}


@respx.mock
async def test_get_linked_incidents_happy_path(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/tickets/1/incidents.json").mock(
        return_value=httpx.Response(200, json=INCIDENTS_PAYLOAD)
    )
    result = await _get_linked_incidents(zendesk_client, 1)
    assert "Ticket #1" in result
    assert "#50" in result
    assert "Cannot login" in result
    assert "Agent Smith" in result
    assert "#51" in result
    assert "App crash on startup" in result
    assert "Unassigned" in result


@respx.mock
async def test_get_linked_incidents_empty(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/tickets/1/incidents.json").mock(
        return_value=httpx.Response(200, json={"tickets": [], "users": []})
    )
    result = await _get_linked_incidents(zendesk_client, 1)
    assert result == "No incidents linked to ticket #1."


@respx.mock
async def test_get_linked_incidents_not_found(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/tickets/99999/incidents.json").mock(
        return_value=httpx.Response(404)
    )
    result = await _get_linked_incidents(zendesk_client, 99999)
    assert result == "Ticket 99999 not found"


@respx.mock
async def test_get_linked_incidents_propagates_errors(
    zendesk_client: ZendeskClient,
) -> None:
    respx.get(f"{BASE}/api/v2/tickets/1/incidents.json").mock(
        return_value=httpx.Response(403)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await _get_linked_incidents(zendesk_client, 1)


# ---------------------------------------------------------------------------
# get_tickets_count_by_status
# ---------------------------------------------------------------------------


@respx.mock
async def test_get_tickets_count_by_status(zendesk_client: ZendeskClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        query = request.url.params.get("query", "")
        counts = {
            "type:ticket status:new": 5,
            "type:ticket status:open": 42,
            "type:ticket status:pending": 10,
            "type:ticket status:hold": 2,
            "type:ticket status:solved": 100,
            "type:ticket status:closed": 500,
        }
        return httpx.Response(200, json={"count": counts.get(query, 0)})

    respx.get(f"{BASE}/api/v2/search/count.json").mock(side_effect=handler)
    result = await _get_tickets_count_by_status(zendesk_client)
    assert "new: 5" in result
    assert "open: 42" in result
    assert "pending: 10" in result
    assert "hold: 2" in result
    assert "solved: 100" in result
    assert "closed: 500" in result
    assert "total: 659" in result


@respx.mock
async def test_get_tickets_count_by_status_propagates_errors(
    zendesk_client: ZendeskClient,
) -> None:
    respx.get(f"{BASE}/api/v2/search/count.json").mock(return_value=httpx.Response(403))
    with pytest.raises(httpx.HTTPStatusError):
        await _get_tickets_count_by_status(zendesk_client)
