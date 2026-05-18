import asyncio

import httpx
from loguru import logger

from zendesk_mcp_ro.config import Settings


class ZendeskClient:
    def __init__(self, settings: Settings) -> None:
        self._max_retries = settings.zendesk_max_retries
        self._client = httpx.AsyncClient(
            base_url=f"https://{settings.zendesk_subdomain}.zendesk.com",
            auth=(
                f"{settings.zendesk_email}/token",
                settings.zendesk_token.get_secret_value(),
            ),
            timeout=settings.zendesk_timeout,
            headers={"Content-Type": "application/json"},
        )

    async def get(self, path: str, params: dict[str, str] | None = None) -> dict:  # type: ignore[type-arg]
        for attempt in range(self._max_retries + 1):
            logger.debug("GET {}", path)
            response = await self._client.get(path, params=params or {})
            logger.debug("{} {}", response.status_code, path)

            if response.status_code in (401, 403, 404):
                response.raise_for_status()

            if response.status_code == 429 or response.status_code >= 500:
                if attempt < self._max_retries:
                    wait = 2**attempt
                    logger.warning(
                        "Retry {}/{} after {} — waiting {}s",
                        attempt + 1,
                        self._max_retries,
                        response.status_code,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    continue
                response.raise_for_status()

            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

        raise RuntimeError("Exhausted retries")

    async def aclose(self) -> None:
        await self._client.aclose()
