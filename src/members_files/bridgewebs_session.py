import os
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv
from playwright.sync_api import (
    Error as PlaywrightError,
)
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import (
    sync_playwright,
)

from members_files.constants import DOWNLOADS_DIR

load_dotenv()


BRIDGEWEBS_LOGIN_URL = (
    "https://www.bridgewebs.com/cgi-bin/bwor/bw.cgi?"
    "pid=upload_menu&wd=1&club=Phoenix"
)


class WebSessionError(Exception):
    """Exception raised for web session-related errors."""


@dataclass
class SessionConfig:
    date: str
    club_name: str
    club_id: str
    contact_name: str
    charge_rate: str


class BridgeWebsSession:
    """Own the browser so it stays open between button clicks."""

    def __init__(self, headless: bool = False) -> None:
        self.session = None
        self._playwright = sync_playwright().start()
        self.logged_in = False
        self._browser = self._playwright.chromium.launch(headless=headless)
        try:
            self._context = self._browser.new_context(
                viewport={"width": 1700, "height": 900}
            )
            self.page = self._context.new_page()
        except PlaywrightError:
            self._playwright.stop()
            raise

    def _login(self) -> None:
        page = self.page
        if self.logged_in:
            return
        try:
            page.goto(
                BRIDGEWEBS_LOGIN_URL,
                wait_until="domcontentloaded",
                timeout=30000,
            )
            page.locator("#bridge_login").wait_for(timeout=15000)
            page.locator("#bridge_login").fill(
                os.getenv("BRIDGEWEBS_USERNAME")
            )
            page.locator("#bridge_password").fill(
                os.getenv("BRIDGEWEBS_PASSWORD")
            )
            page.locator("#bridge_password").press("Enter")

        except PlaywrightTimeoutError as error:
            self.close()
            raise WebSessionError(
                "Page did not load in time. Check your connection and "
                "try again."
            ) from error
        except PlaywrightError as error:
            self.close()
            raise WebSessionError(
                f"Could not reach BridgeWebs: {error}"
            ) from error

        self.logged_in = True

    def download_members_file(self) -> None:
        """Download the members file from BridgeWebs."""
        self._login()

        page = self.page
        page.get_by_role("link", name="Membership", exact=True).click()
        page.get_by_role("link", name="Import/Export").click()
        link = page.get_by_text("Download", exact=True)

        with page.expect_download(timeout=30000) as info:
            link.click()

        download = info.value
        file_name = f"membership_{datetime.now().strftime('%Y%m%d')}.csv"

        target = DOWNLOADS_DIR / file_name
        download.save_as(target)
        self.close()

    def close(self) -> None:
        self._context.close()
        self._playwright.stop()


def get_bridgewebs_session(
    existing_session: BridgeWebsSession = None,
) -> BridgeWebsSession:
    """Reuse the open session, or replace one you have closed."""
    session = existing_session
    if session is not None and not session.is_alive():
        session.close()  # Stops Playwright, so a new start() works
        session = None
    if session is None:
        session = BridgeWebsSession()
    return session
