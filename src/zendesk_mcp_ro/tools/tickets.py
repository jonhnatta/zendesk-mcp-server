import httpx
from fastmcp import FastMCP

from zendesk_mcp_ro.client import ZendeskClient


async def _get_ticket(client: ZendeskClient, ticket_id: int) -> str:
    try:
        data = await client.get(f"/api/v2/tickets/{ticket_id}.json")
        ticket = data["ticket"]
        return (
            f"Ticket #{ticket['id']}: {ticket['subject']}\n"
            f"Status: {ticket['status']} | Priority: {ticket.get('priority', 'normal')}"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Ticket {ticket_id} not found"
        raise


def register(mcp: FastMCP, client: ZendeskClient) -> None:
    @mcp.tool()
    async def get_ticket(ticket_id: int) -> str:
        """Retrieve a Zendesk ticket by its ID.

        Returns the ticket subject, status, and priority.
        Use this when you need details about a specific support ticket.
        """
        return await _get_ticket(client, ticket_id)
