import httpx
from fastmcp import FastMCP

from zendesk_mcp_ro.client import ZendeskClient


async def _get_user(client: ZendeskClient, user_id: int) -> str:
    try:
        data = await client.get(
            f"/api/v2/users/{user_id}.json",
            params={"include": "organizations"},
        )
        u = data["user"]
        orgs: list[dict[str, object]] = data.get("organizations", [])

        org_name = next(
            (
                str(o.get("name", "unknown"))
                for o in orgs
                if o.get("id") == u.get("organization_id")
            ),
            "none",
        )
        tags = ", ".join(u.get("tags", [])) or "none"

        return (
            f"User #{u['id']}: {u['name']}\n"
            f"Email: {u.get('email', 'n/a')} | Role: {u.get('role', 'n/a')}\n"
            f"Phone: {u.get('phone') or 'n/a'} | Time Zone: {u.get('time_zone', 'n/a')}\n"
            f"Organization: {org_name}\n"
            f"Tags: {tags}\n"
            f"Active: {u.get('active')} | Suspended: {u.get('suspended')}\n"
            f"Created: {u.get('created_at')} | Updated: {u.get('updated_at')}"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"User {user_id} not found"
        raise


def _format_user_list(
    users: list[dict[str, object]],
    total: int,
    label: str,
) -> str:
    lines = [f"{label} (Showing {len(users)} of {total}):\n"]
    for u in users:
        lines.append(
            f"#{u['id']} — {u.get('name', '(no name)')}\n"
            f"  Email: {u.get('email', 'n/a')} | Role: {u.get('role', 'n/a')}\n"
            f"  Updated: {u.get('updated_at')}\n"
        )
    return "\n".join(lines)


async def _search_users(
    client: ZendeskClient,
    query: str,
    per_page: int = 25,
) -> str:
    data = await client.get(
        "/api/v2/users/search.json",
        params={"query": query, "per_page": str(per_page)},
    )
    users: list[dict[str, object]] = data.get("users", [])
    total: int = int(str(data.get("count", 0)))

    if not users:
        return f"No users found for query: {query}"

    return _format_user_list(users, total, f'Search results for "{query}"')


def register(mcp: FastMCP, client: ZendeskClient) -> None:
    @mcp.tool()
    async def get_user(user_id: int) -> str:
        """Retrieve a Zendesk user by their ID.

        Returns name, email, role, phone, time zone, organization, tags,
        active/suspended status, and timestamps.
        Use this when you need full details about a specific agent, admin, or end-user.
        """
        return await _get_user(client, user_id)

    @mcp.tool()
    async def search_users(query: str, per_page: int = 25) -> str:
        """Search Zendesk users by name, email, or other attributes.

        Returns a paginated list of matching users with name, email, role,
        and last update time.
        Accepts partial matches (e.g. a first name, email domain, or role).
        Use this when you need to find a specific agent or end-user by name or email.
        """
        return await _search_users(client, query, per_page)
