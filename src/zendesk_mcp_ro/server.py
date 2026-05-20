import sys

from fastmcp import FastMCP
from loguru import logger

from zendesk_mcp_ro.client import ZendeskClient
from zendesk_mcp_ro.config import ConfigurationError, Settings, get_settings
from zendesk_mcp_ro.tools import metrics, organizations, tickets, users


def _create_app(settings: Settings) -> tuple[FastMCP, ZendeskClient]:
    client = ZendeskClient(settings)
    mcp = FastMCP(
        "zendesk-mcp-ro",
        instructions=(
            "Read-only MCP server for Zendesk. "
            "Use the available tools to query tickets, users, organizations and metrics."
        ),
    )
    tickets.register(mcp, client)
    users.register(mcp, client)
    organizations.register(mcp, client)
    metrics.register(mcp, client)
    return mcp, client


def main() -> None:
    try:
        settings = get_settings()
    except ConfigurationError as e:
        logger.error("ConfigurationError: {}", e)
        sys.exit(1)

    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)

    mcp, _ = _create_app(settings)

    logger.info(
        "Zendesk MCP Server starting (subdomain={})", settings.zendesk_subdomain
    )
    logger.info("Configuration OK — tools registered")

    mcp.run()
