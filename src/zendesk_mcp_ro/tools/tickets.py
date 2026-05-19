import httpx
from fastmcp import FastMCP

from zendesk_mcp_ro.client import ZendeskClient


def _find_name(users: list[dict[str, object]], user_id: object) -> str:
    for u in users:
        if u.get("id") == user_id:
            return str(u.get("name", "unknown"))
    return "unknown"


async def _get_ticket(client: ZendeskClient, ticket_id: int) -> str:
    try:
        data = await client.get(
            f"/api/v2/tickets/{ticket_id}.json",
            params={"include": "users,organizations"},
        )
        t = data["ticket"]
        users: list[dict[str, object]] = data.get("users", [])
        orgs: list[dict[str, object]] = data.get("organizations", [])

        org_name = next(
            (
                str(o.get("name", "unknown"))
                for o in orgs
                if o.get("id") == t.get("organization_id")
            ),
            "unknown",
        )
        tags = ", ".join(t.get("tags", [])) or "none"
        csat = t.get("satisfaction_rating")
        csat_str = csat.get("score", "n/a") if isinstance(csat, dict) else "n/a"
        channel = t.get("via", {}).get("channel", "unknown")

        return (
            f"Ticket #{t['id']}: {t['subject']}\n"
            f"Type: {t.get('type', 'n/a')} | Status: {t['status']} | Priority: {t.get('priority', 'normal')}\n"
            f"Channel: {channel} | CSAT: {csat_str}\n"
            f"Requester: {_find_name(users, t.get('requester_id'))} | Assignee: {_find_name(users, t.get('assignee_id'))}\n"
            f"Organization: {org_name}\n"
            f"Tags: {tags}\n"
            f"Created: {t.get('created_at')} | Updated: {t.get('updated_at')}\n"
            f"Description: {t.get('description', '')}"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Ticket {ticket_id} not found"
        raise


def register(mcp: FastMCP, client: ZendeskClient) -> None:
    @mcp.tool()
    async def get_ticket(ticket_id: int) -> str:
        """Retrieve a Zendesk ticket by its ID.

        Returns subject, type, status, priority, channel, CSAT, requester,
        assignee, organization, tags, timestamps, and description.
        Use this when you need full details about a specific support ticket.
        """
        return await _get_ticket(client, ticket_id)
