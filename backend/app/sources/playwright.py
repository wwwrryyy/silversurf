import logging
from app.config import settings
from app.core.errors import SourceFetchError
from app.sources.base import RawScrapeResult
from app.sources.ibja_html import IbjaHtmlSource

logger = logging.getLogger(__name__)


class PlaywrightFallbackSource:
    """
    Fallback fetcher launched if plain HTTP parse fails validation twice consecutively.
    Renders JavaScript using headless Chromium before passing HTML to IbjaHtmlSource.
    """

    def __init__(
        self,
        source_url: str | None = None,
        user_agent: str | None = None,
        timeout: float | None = None,
    ):
        self.source_url = source_url or settings.source_url
        self.user_agent = user_agent or settings.user_agent
        self.timeout = timeout or settings.request_timeout_seconds
        self.parser = IbjaHtmlSource(
            source_url=self.source_url, user_agent=self.user_agent, timeout=self.timeout
        )

    async def fetch_latest(self) -> list[RawScrapeResult]:
        logger.warning(
            "Invoking PlaywrightFallbackSource for JS-rendered extraction from %s",
            self.source_url,
        )
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=self.user_agent)
                await page.goto(self.source_url, timeout=int(self.timeout * 1000))
                await page.wait_for_selector("table", timeout=int(self.timeout * 1000))
                content = await page.content()
                await browser.close()
                raw_bytes = content.encode("utf-8")
        except ImportError:
            logger.info("Playwright not installed, falling back to HTTP fetcher")
            return await self.parser.fetch_latest()
        except Exception as exc:
            logger.error("Playwright fetch failed: %s", exc)
            raise SourceFetchError(f"Playwright fallback failed: {exc}") from exc

        return self.parser.parse_html(
            raw_bytes=raw_bytes, http_status=200, source_url=self.source_url
        )

    async def fetch_historical_pdf(self, pdf_url: str) -> list[RawScrapeResult]:
        return await self.parser.fetch_historical_pdf(pdf_url)
