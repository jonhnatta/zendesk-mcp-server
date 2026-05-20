import httpx
from fastmcp import FastMCP

from zendesk_mcp_ro.client import ZendeskClient


async def _get_organization(client: ZendeskClient, org_id: int) -> str:
    try:
        data = await client.get(f"/api/v2/organizations/{org_id}.json")
        o = data["organization"]

        domains = ", ".join(o.get("domain_names", [])) or "none"
        tags = ", ".join(o.get("tags", [])) or "none"
        notes = o.get("notes") or "n/a"
        details = o.get("details") or "n/a"
        group_id = o.get("group_id") or "n/a"

        return (
            f"Organization #{o['id']}: {o['name']}\n"
            f"Domains: {domains}\n"
            f"Tags: {tags}\n"
            f"Notes: {notes}\n"
            f"Details: {details}\n"
            f"Group ID: {group_id}\n"
            f"Created: {o.get('created_at')} | Updated: {o.get('updated_at')}"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Organization {org_id} not found"
        raise


def _format_org_list(
    orgs: list[dict[str, object]],
    total: int,
    label: str,
) -> str:
    lines = [f"{label} (Showing {len(orgs)} of {total}):\n"]
    for o in orgs:
        domains = ", ".join(o.get("domain_names", [])) or "none"  # type: ignore[arg-type]
        lines.append(
            f"#{o['id']} — {o.get('name', '(no name)')}\n"
            f"  Domains: {domains}\n"
            f"  Updated: {o.get('updated_at')}\n"
        )
    return "\n".join(lines)


async def _list_organizations(
    client: ZendeskClient,
    per_page: int = 25,
) -> str:
    data = await client.get(
        "/api/v2/organizations.json",
        params={"per_page": str(per_page)},
    )
    orgs: list[dict[str, object]] = data.get("organizations", [])
    total: int = int(str(data.get("count", 0)))

    if not orgs:
        return "No organizations found."

    return _format_org_list(orgs, total, "Organizations")


def register(mcp: FastMCP, client: ZendeskClient) -> None:
    @mcp.tool()
    async def get_organization(org_id: int) -> str:
        """Retrieve a Zendesk organization by its ID.

        Returns name, domain names, tags, notes, details, group ID,
        and timestamps.
        Use this when you need full details about a specific customer organization.
        """
        return await _get_organization(client, org_id)

    @mcp.tool()
    async def list_organizations(per_page: int = 25) -> str:
        """List all Zendesk organizations.

        Returns a paginated list of organizations with name, domain names,
        and last update time, sorted by Zendesk default order.
        Use this when you need an overview of all organizations in your account.
        """
        return await _list_organizations(client, per_page)
