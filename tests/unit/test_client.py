import asyncio

import httpx
import pytest
import respx

from zendesk_mcp_ro.client import ZendeskClient

BASE = "https://test-company.zendesk.com"


@respx.mock
async def test_get_returns_json(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/tickets/1").mock(
        return_value=httpx.Response(200, json={"ticket": {"id": 1}})
    )
    result = await zendesk_client.get("/api/v2/tickets/1")
    assert result == {"ticket": {"id": 1}}


@respx.mock
async def test_get_retries_on_429(
    zendesk_client: ZendeskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    sleep_calls: list[float] = []

    async def mock_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)

    route = respx.get(f"{BASE}/api/v2/tickets/1")
    route.side_effect = [
        httpx.Response(429),
        httpx.Response(200, json={"ticket": {"id": 1}}),
    ]

    result = await zendesk_client.get("/api/v2/tickets/1")
    assert result == {"ticket": {"id": 1}}
    assert route.call_count == 2
    assert sleep_calls == [1]


@respx.mock
async def test_get_retries_on_5xx_and_raises_after_exhaustion(
    zendesk_client: ZendeskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        asyncio, "sleep", lambda _: asyncio.coroutines.coroutine(lambda: None)()
    )

    async def mock_sleep(_: float) -> None:
        pass

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)

    respx.get(f"{BASE}/api/v2/tickets/1").mock(return_value=httpx.Response(500))

    with pytest.raises(httpx.HTTPStatusError):
        await zendesk_client.get("/api/v2/tickets/1")


@respx.mock
async def test_get_fails_fast_on_401(zendesk_client: ZendeskClient) -> None:
    route = respx.get(f"{BASE}/api/v2/tickets/1").mock(return_value=httpx.Response(401))
    with pytest.raises(httpx.HTTPStatusError):
        await zendesk_client.get("/api/v2/tickets/1")
    assert route.call_count == 1


@respx.mock
async def test_get_fails_fast_on_403(zendesk_client: ZendeskClient) -> None:
    route = respx.get(f"{BASE}/api/v2/tickets/1").mock(return_value=httpx.Response(403))
    with pytest.raises(httpx.HTTPStatusError):
        await zendesk_client.get("/api/v2/tickets/1")
    assert route.call_count == 1


@respx.mock
async def test_get_fails_fast_on_404(zendesk_client: ZendeskClient) -> None:
    route = respx.get(f"{BASE}/api/v2/tickets/1").mock(return_value=httpx.Response(404))
    with pytest.raises(httpx.HTTPStatusError):
        await zendesk_client.get("/api/v2/tickets/1")
    assert route.call_count == 1


def test_token_not_in_repr(zendesk_client: ZendeskClient) -> None:
    assert "secret-token" not in repr(zendesk_client)
    assert "secret-token" not in str(zendesk_client)
