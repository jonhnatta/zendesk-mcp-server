import httpx
from fastmcp import FastMCP

from zendesk_mcp_ro.client import ZendeskClient


def _find_name(users: list[dict[str, object]], user_id: object) -> str:
    if user_id is None:
        return "Unassigned"
    for u in users:
        if u.get("id") == user_id:
            return str(u.get("name", "unknown"))
    return "unknown"


async def _get_ticket(client: ZendeskClient, ticket_id: int) -> str:
    try:
        data = await client.get(
            f"/api/v2/tickets/{ticket_id}.json",
            params={"include": "users,organizations,groups"},
        )
        t = data["ticket"]
        users: list[dict[str, object]] = data.get("users", [])
        orgs: list[dict[str, object]] = data.get("organizations", [])
        groups: list[dict[str, object]] = data.get("groups", [])

        org_name = next(
            (
                str(o.get("name", "unknown"))
                for o in orgs
                if o.get("id") == t.get("organization_id")
            ),
            "unknown",
        )
        group_name = next(
            (
                str(g.get("name", "unknown"))
                for g in groups
                if g.get("id") == t.get("group_id")
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
            f"Organization: {org_name} | Group: {group_name}\n"
            f"Tags: {tags}\n"
            f"Created: {t.get('created_at')} | Updated: {t.get('updated_at')}\n"
            f"Description: {t.get('description', '')}"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Ticket {ticket_id} not found"
        raise


async def _get_ticket_comments(
    client: ZendeskClient,
    ticket_id: int,
    include_internal: bool = False,
) -> str:
    try:
        data = await client.get(
            f"/api/v2/tickets/{ticket_id}/comments.json",
            params={"include": "users"},
        )
        all_comments: list[dict[str, object]] = data.get("comments", [])
        users: list[dict[str, object]] = data.get("users", [])

        comments = (
            all_comments
            if include_internal
            else [c for c in all_comments if c.get("public", True)]
        )

        if not comments:
            return f"Ticket #{ticket_id} has no comments."

        lines = [f"Comments for Ticket #{ticket_id} ({len(comments)} shown):\n"]
        for i, c in enumerate(comments, 1):
            author = _find_name(users, c.get("author_id"))
            created = c.get("created_at", "unknown")
            visibility = "public" if c.get("public", True) else "internal"
            body = str(c.get("body", "")).strip()
            lines.append(f"[{i}] {author} — {created} ({visibility})\n{body}\n")

        return "\n".join(lines)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Ticket {ticket_id} not found"
        raise


def _fmt_minutes(val: object) -> str:
    if val is None:
        return "n/a"
    minutes = int(str(val))
    if minutes < 60:
        return f"{minutes}m"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}m"


async def _get_ticket_metrics(client: ZendeskClient, ticket_id: int) -> str:
    try:
        data = await client.get(f"/api/v2/tickets/{ticket_id}/metrics.json")
        m = data.get("ticket_metric", {})

        reply_raw = m.get("reply_time_in_minutes")
        reply_minutes = (
            reply_raw.get("calendar") if isinstance(reply_raw, dict) else reply_raw
        )

        resolution_raw = m.get("full_resolution_time_in_minutes")
        resolution_minutes = (
            resolution_raw.get("calendar")
            if isinstance(resolution_raw, dict)
            else resolution_raw
        )

        return (
            f"Metrics for Ticket #{ticket_id}:\n"
            f"First Reply Time: {_fmt_minutes(reply_minutes)}\n"
            f"Full Resolution Time: {_fmt_minutes(resolution_minutes)}\n"
            f"Reopens: {m.get('reopens', 0)}\n"
            f"Replies: {m.get('replies', 0)}\n"
            f"Assignee Updated: {m.get('assignee_updated_at') or 'n/a'}\n"
            f"Requester Updated: {m.get('requester_updated_at') or 'n/a'}"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Ticket {ticket_id} not found"
        raise


def _format_ticket_list(
    tickets: list[dict[str, object]],
    users: list[dict[str, object]],
    total: int,
    label: str,
) -> str:
    lines = [f"{label} (Showing {len(tickets)} of {total}):\n"]
    for t in tickets:
        assignee = _find_name(users, t.get("assignee_id"))
        lines.append(
            f"#{t['id']} — {t.get('subject', '(no subject)')}\n"
            f"  Status: {t.get('status')} | Priority: {t.get('priority', 'normal')}"
            f" | Assignee: {assignee}\n"
            f"  Updated: {t.get('updated_at')}\n"
        )
    return "\n".join(lines)


async def _search_tickets(
    client: ZendeskClient,
    query: str,
    per_page: int = 25,
) -> str:
    data = await client.get(
        "/api/v2/search.json",
        params={
            "query": f"type:ticket {query}",
            "per_page": str(per_page),
            "include": "users",
        },
    )
    results: list[dict[str, object]] = data.get("results", [])
    users: list[dict[str, object]] = data.get("users", [])
    total: int = int(str(data.get("count", 0)))

    if not results:
        return f"No tickets found for query: {query}"

    return _format_ticket_list(results, users, total, f'Search results for "{query}"')


def register(mcp: FastMCP, client: ZendeskClient) -> None:
    @mcp.tool()
    async def get_ticket(ticket_id: int) -> str:
        """Retrieve a Zendesk ticket by its ID.

        Returns subject, type, status, priority, channel, CSAT, requester,
        assignee, organization, tags, timestamps, and description.
        Use this when you need full details about a specific support ticket.
        """
        return await _get_ticket(client, ticket_id)

    @mcp.tool()
    async def get_ticket_comments(
        ticket_id: int,
        include_internal: bool = False,
    ) -> str:
        """Retrieve all comments (conversation thread) for a Zendesk ticket.

        Returns each comment with author name, timestamp, visibility
        (public/internal), and body text. By default only public comments
        are returned. Set include_internal=True to also include internal
        agent notes.
        Use this when you need to see the full conversation of a support ticket.
        """
        return await _get_ticket_comments(client, ticket_id, include_internal)

    @mcp.tool()
    async def get_ticket_metrics(ticket_id: int) -> str:
        """Retrieve SLA and performance metrics for a Zendesk ticket.

        Returns first reply time, full resolution time, number of reopens,
        number of replies, and last update timestamps for assignee and requester.
        Use this when you need to evaluate response times or SLA compliance
        for a ticket.
        """
        return await _get_ticket_metrics(client, ticket_id)

    @mcp.tool()
    async def search_tickets(query: str, per_page: int = 25) -> str:
        """Search Zendesk tickets using a text query.

        Accepts free-text search terms and returns a paginated list of matching
        tickets with subject, status, priority, assignee and last update time.
        Supports Zendesk search syntax (e.g. 'status:open assignee:me tag:billing').
        Use this when you need to find tickets matching specific keywords or filters.
        """
        return await _search_tickets(client, query, per_page)
