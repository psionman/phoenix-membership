import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from . import logger

load_dotenv()

BBO_LOGIN_URL = "https://www.bridgebase.com/v3/auth/login"
SESSION_FILE = Path("bbo_session.json")

BBO_USERNAME = os.getenv("BBO_USERNAME")
BBO_PASSWORD = os.getenv("BBO_PASSWORD")

SESSION_PATTERN = re.compile(r"#(\d+)\s+.*?\b(\d{1,2} [A-Za-z]+ \d{4})\b")
COOKIE_BUTTON = re.compile(r"accept|agree|allow", re.IGNORECASE)
COOKIE_TIMEOUT = 1000


class WebSessionError(Exception):
    """Exception raised for web session-related errors."""


@dataclass
class Session:
    number: str
    date: date


class BboPhoenixSession:
    """Own the browser so it stays open between button clicks."""

    def __init__(self, headless: bool = False) -> None:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=headless)
        self.logged_in = False
        try:
            self._context = self._browser.new_context(
                viewport={"width": 1700, "height": 900}
            )
        except Exception as e:
            logger.error(f"Failed to create browser context: {e}")
            raise
        self.page: Page = self._context.new_page()
        # Set Chromium page zoom to 75%
        cdp = self._context.new_cdp_session(self.page)
        cdp.send("Emulation.setPageScaleFactor", {"pageScaleFactor": 0.75})

    def _login(self) -> None:
        page = self.page
        if self.logged_in:
            return

        try:
            page.goto(
                BBO_LOGIN_URL, wait_until="domcontentloaded", timeout=30000
            )
            page.locator("#username").wait_for(timeout=15000)
        except PlaywrightTimeoutError as error:
            self.close()
            raise WebSessionError(
                "BBO did not load in time. Check your connection and "
                "try again."
            ) from error
        except PlaywrightError as error:
            self.close()
            raise WebSessionError(f"Could not reach BBO: {error}") from error

        self._accept_cookies(page)

        self._enter_credentials(BBO_USERNAME, BBO_PASSWORD)
        page.wait_for_url(lambda url: "/auth/login" not in url)
        page.add_style_tag(content="body { zoom: 75%; }")
        self._context.storage_state(path=SESSION_FILE)

        self.logged_in = True

    def _enter_credentials(self, username: str, password: str) -> None:
        page = self.page
        page.locator("#username").fill(username)
        page.locator("#password").fill(password)
        page.locator("#password").press("Enter")

    def get_current_sessions(self) -> list[str]:
        self._login()
        page = self.page
        page.locator('mat-icon[data-mat-icon-name="director"]').click()
        page.get_by_role("tab", name="Pending Tournaments").click()
        return self._get_session_dates()

    def _get_session_dates(self, timeout: int = 15000) -> list[datetime]:
        """Return the start of every 'Starts: ...' entry as a datetime."""
        page = self.page
        page.wait_for_function(
            "(pattern) => new RegExp(pattern).test(document.body.innerText)",
            arg=SESSION_PATTERN.pattern,
            timeout=timeout,
        )
        text = page.locator("body").inner_text()
        found = []
        for match in SESSION_PATTERN.finditer(text):
            try:
                when = datetime.strptime(match.group(2), "%d %B %Y").date()
            except ValueError:
                continue
            found.append(Session(number=match.group(1), date=when))
        return found

    def _accept_cookies(self, page: Page) -> None:
        """Click the cookie consent button if one appears."""
        button = page.get_by_role("button", name=COOKIE_BUTTON).first
        try:
            button.click(timeout=COOKIE_TIMEOUT)
        except PlaywrightTimeoutError:
            pass  # No banner this time

    def close(self) -> None:
        self._browser.close()
        self._playwright.stop()
