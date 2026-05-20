import httpx
import pytest
import respx

from zendesk_mcp_ro.client import ZendeskClient
from zendesk_mcp_ro.tools.organizations import (
    _get_organization,
    _list_organizations,
)

BASE = "https://test-company.zendesk.com"

ORG_PAYLOAD = {
    "organization": {
        "id": 303,
        "name": "Acme Corp",
        "domain_names": ["acme.com", "acme.org"],
        "tags": ["enterprise", "vip"],
        "notes": "Key account",
        "details": "Fortune 500 company",
        "group_id": 404,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-06-01T00:00:00Z",
    }
}


@respx.mock
async def test_get_organization_happy_path(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/organizations/303.json").mock(
        return_value=httpx.Response(200, json=ORG_PAYLOAD)
    )
    result = await _get_organization(zendesk_client, 303)
    assert "Organization #303" in result
    assert "Acme Corp" in result
    assert "acme.com" in result
    assert "acme.org" in result
    assert "enterprise" in result
    assert "vip" in result
    assert "Key account" in result
    assert "Fortune 500 company" in result


@respx.mock
async def test_get_organization_no_domains_no_tags(
    zendesk_client: ZendeskClient,
) -> None:
    payload = {
        "organization": {
            "id": 304,
            "name": "Empty Corp",
            "domain_names": [],
            "tags": [],
            "notes": None,
            "details": None,
            "group_id": None,
            "created_at": "2024-02-01T00:00:00Z",
            "updated_at": "2024-02-01T00:00:00Z",
        }
    }
    respx.get(f"{BASE}/api/v2/organizations/304.json").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = await _get_organization(zendesk_client, 304)
    assert "Empty Corp" in result
    assert "Domains: none" in result
    assert "Tags: none" in result
    assert "Notes: n/a" in result
    assert "Details: n/a" in result
    assert "Group ID: n/a" in result


@respx.mock
async def test_get_organization_not_found(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/organizations/99999.json").mock(
        return_value=httpx.Response(404)
    )
    result = await _get_organization(zendesk_client, 99999)
    assert result == "Organization 99999 not found"


@respx.mock
async def test_get_organization_propagates_errors(
    zendesk_client: ZendeskClient,
) -> None:
    respx.get(f"{BASE}/api/v2/organizations/303.json").mock(
        return_value=httpx.Response(403)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await _get_organization(zendesk_client, 303)


# ---------------------------------------------------------------------------
# list_organizations
# ---------------------------------------------------------------------------

LIST_ORGS_PAYLOAD = {
    "organizations": [
        {
            "id": 303,
            "name": "Acme Corp",
            "domain_names": ["acme.com"],
            "updated_at": "2024-06-01T00:00:00Z",
        },
        {
            "id": 304,
            "name": "Beta Ltd",
            "domain_names": [],
            "updated_at": "2024-05-01T00:00:00Z",
        },
    ],
    "count": 42,
}


@respx.mock
async def test_list_organizations_returns_list(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/organizations.json").mock(
        return_value=httpx.Response(200, json=LIST_ORGS_PAYLOAD)
    )
    result = await _list_organizations(zendesk_client)
    assert "Showing 2 of 42" in result
    assert "#303" in result
    assert "Acme Corp" in result
    assert "acme.com" in result
    assert "#304" in result
    assert "Beta Ltd" in result


@respx.mock
async def test_list_organizations_empty(zendesk_client: ZendeskClient) -> None:
    respx.get(f"{BASE}/api/v2/organizations.json").mock(
        return_value=httpx.Response(200, json={"organizations": [], "count": 0})
    )
    result = await _list_organizations(zendesk_client)
    assert result == "No organizations found."


@respx.mock
async def test_list_organizations_propagates_errors(
    zendesk_client: ZendeskClient,
) -> None:
    respx.get(f"{BASE}/api/v2/organizations.json").mock(
        return_value=httpx.Response(403)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await _list_organizations(zendesk_client)
