import httpx
import pytest
import respx

from zendesk_mcp_ro.client import ZendeskClient
from zendesk_mcp_ro.tools.metrics import _list_satisfaction_ratings

BASE = "https://test-company.zendesk.com"

RATINGS_PAYLOAD = {
    "satisfaction_ratings": [
        {
            "id": 1,
            "score": "good",
            "comment": "Great support!",
            "ticket_id": 101,
            "requester_id": 201,
            "assignee_id": 301,
            "created_at": "2024-06-01T10:00:00Z",
            "updated_at": "2024-06-01T10:00:00Z",
        },
        {
            "id": 2,
            "score": "bad",
            "comment": None,
            "ticket_id": 102,
            "requester_id": 202,
            "assignee_id": 302,
            "created_at": "2024-06-02T10:00:00Z",
            "updated_at": "2024-06-02T10:00:00Z",
        },
    ],
    "count": 42,
}


@respx.mock
async def test_list_satisfaction_ratings_no_filter(
    zendesk_client: ZendeskClient,
) -> None:
    respx.get(f"{BASE}/api/v2/satisfaction_ratings.json").mock(
        return_value=httpx.Response(200, json=RATINGS_PAYLOAD)
    )
    result = await _list_satisfaction_ratings(zendesk_client)
    assert "Showing 2 of 42" in result
    assert "#1" in result
    assert "Ticket #101" in result
    assert "good" in result
    assert "Great support!" in result
    assert "#2" in result
    assert "Ticket #102" in result
    assert "bad" in result
    assert "no comment" in result


@respx.mock
async def test_list_satisfaction_ratings_filter_by_score(
    zendesk_client: ZendeskClient,
) -> None:
    payload = {
        "satisfaction_ratings": [
            {
                "id": 1,
                "score": "good",
                "comment": "Great support!",
                "ticket_id": 101,
                "requester_id": 201,
                "assignee_id": 301,
                "created_at": "2024-06-01T10:00:00Z",
                "updated_at": "2024-06-01T10:00:00Z",
            }
        ],
        "count": 30,
    }
    respx.get(f"{BASE}/api/v2/satisfaction_ratings.json").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = await _list_satisfaction_ratings(zendesk_client, score="good")
    assert "score=good" in result
    assert "Showing 1 of 30" in result
    assert "good" in result


@respx.mock
async def test_list_satisfaction_ratings_empty_no_filter(
    zendesk_client: ZendeskClient,
) -> None:
    respx.get(f"{BASE}/api/v2/satisfaction_ratings.json").mock(
        return_value=httpx.Response(200, json={"satisfaction_ratings": [], "count": 0})
    )
    result = await _list_satisfaction_ratings(zendesk_client)
    assert result == "No satisfaction ratings found for all scores."


@respx.mock
async def test_list_satisfaction_ratings_empty_with_score_filter(
    zendesk_client: ZendeskClient,
) -> None:
    respx.get(f"{BASE}/api/v2/satisfaction_ratings.json").mock(
        return_value=httpx.Response(200, json={"satisfaction_ratings": [], "count": 0})
    )
    result = await _list_satisfaction_ratings(zendesk_client, score="bad")
    assert result == "No satisfaction ratings found for score=bad."


@respx.mock
async def test_list_satisfaction_ratings_propagates_errors(
    zendesk_client: ZendeskClient,
) -> None:
    respx.get(f"{BASE}/api/v2/satisfaction_ratings.json").mock(
        return_value=httpx.Response(403)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await _list_satisfaction_ratings(zendesk_client)
