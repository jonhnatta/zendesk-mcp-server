from fastmcp import FastMCP

from zendesk_mcp_ro.client import ZendeskClient


def _format_csat_list(
    ratings: list[dict[str, object]],
    total: int,
    label: str,
) -> str:
    lines = [f"{label} (Showing {len(ratings)} of {total}):\n"]
    for r in ratings:
        comment = str(r.get("comment") or "no comment")
        lines.append(
            f"#{r['id']} — Ticket #{r.get('ticket_id')} | Score: {r.get('score')}\n"
            f"  Comment: {comment}\n"
            f"  Created: {r.get('created_at')}\n"
        )
    return "\n".join(lines)


async def _list_satisfaction_ratings(
    client: ZendeskClient,
    score: str | None = None,
    per_page: int = 25,
) -> str:
    params: dict[str, str] = {"per_page": str(per_page)}
    if score:
        params["score"] = score

    data = await client.get(
        "/api/v2/satisfaction_ratings.json",
        params=params,
    )
    ratings: list[dict[str, object]] = data.get("satisfaction_ratings", [])
    total: int = int(str(data.get("count", 0)))

    if not ratings:
        empty_label = f"score={score}" if score else "all scores"
        return f"No satisfaction ratings found for {empty_label}."

    label = f"Satisfaction ratings (score={score})" if score else "Satisfaction ratings"
    return _format_csat_list(ratings, total, label)


def register(mcp: FastMCP, client: ZendeskClient) -> None:
    @mcp.tool()
    async def list_satisfaction_ratings(
        score: str | None = None,
        per_page: int = 25,
    ) -> str:
        """List Zendesk satisfaction ratings (CSAT).

        Returns a paginated list of customer satisfaction ratings with
        ticket ID, score (good/bad), and customer comment.
        Use score="good" or score="bad" to filter by rating.
        Omit score to return all ratings regardless of outcome.
        Use this when you need to review customer satisfaction feedback.
        """
        return await _list_satisfaction_ratings(client, score, per_page)
