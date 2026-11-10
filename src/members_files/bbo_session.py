import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import (
    Error as PlaywrightError,
)
from playwright.sync_api import Page, expect, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from members_files.constants import DOWNLOADS_DIR

load_dotenv()

BBO_USERNAME = os.getenv("BBO_USERNAME")
BBO_PASSWORD = os.getenv("BBO_PASSWORD")
COOKIE_TIMEOUT = 1000
COOKIE_BUTTON = re.compile(r"accept|agree|allow", re.IGNORECASE)
BBO_SESSIONS_URL = "https://www.bridgebase.com/v3/auth/login"
SESSION_FILE = Path("bbo_session.json")


class WebSessionError(Exception):
    """Exception raised for web session-related errors."""


@dataclass
class SessionConfig:
    date: str
    club_name: str
    club_id: str
    contact_name: str
    charge_rate: str


class BboSession:
    def __init__(self, headless: bool = False) -> None:
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

        cdp = self._context.new_cdp_session(self.page)
        cdp.send("Emulation.setPageScaleFactor", {"pageScaleFactor": 0.75})

    def is_alive(self) -> bool:
        """True while the browser window is still open and responding."""
        try:
            self.page.evaluate("1")  # Raises if the window was closed
            return True
        except PlaywrightError:
            return False

    def close(self) -> None:
        """Close everything; safe to call more than once."""
        for step in (
            self._context.close,
            self._browser.close,
            self._playwright.stop,
        ):
            try:
                step()
            except PlaywrightError:
                pass  # Already closed, for example by you

    def _login(self) -> None:
        page = self.page
        if self.logged_in:
            return
        try:
            page.goto(
                BBO_SESSIONS_URL, wait_until="domcontentloaded", timeout=30000
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

        accept_cookies(page)

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

    def download_include_list(self) -> None:
        """Download the include list from BBO."""
        self._login()
        page = self.page
        page.on(
            "dialog",
            lambda d: (
                print(f"dialog [{d.type}]: {d.message}", flush=True),
                d.accept(),
            ),
        )

        page.locator("tab-bar-button:visible").filter(
            has_text="Director"
        ).click()
        page.get_by_role("button", name="Include/Exclude Lists").click()
        page.get_by_role("button", name="Manage List").click()

        frame = page.locator("modal-content iframe").content_frame
        username = frame.get_by_role("textbox", name="Username:")
        password = frame.get_by_role("textbox", name="Password:")
        execute = frame.locator("#submit")
        username.wait_for(timeout=10000)

        # Type without clicking: a table cell covers the boxes
        username.press_sequentially(BBO_USERNAME, delay=30)
        password.press_sequentially(BBO_PASSWORD, delay=30)
        frame.get_by_label("Type:").select_option("include")
        frame.get_by_label("Action:").select_option("dw")

        try:
            expect(execute).to_be_enabled(timeout=3000)
        except AssertionError:
            # Nudge the form's own scripts with the events they listen for
            for box in (username, password):
                for event in ("input", "keyup", "change", "blur"):
                    box.dispatch_event(event)
            try:
                expect(execute).to_be_enabled(timeout=3000)
            except AssertionError:
                print("Execute is still disabled. Form state:", flush=True)
                for html in frame.locator("input, select").evaluate_all(
                    "els => els.map(e => e.outerHTML.slice(0, 160))"
                ):
                    print("  ", html, flush=True)
                print(frame.locator("body").inner_text()[:500], flush=True)
                page.screenshot(path="include_list.png")
                return  # Leave the window open to look at

        print("About to click Execute", flush=True)
        try:
            with page.expect_download(timeout=20000) as info:
                # A script click avoids the covering cell
                execute.evaluate("el => el.click()")
        except PlaywrightTimeoutError:
            print("No download. The form now shows:", flush=True)
            print(frame.locator("body").inner_text()[:800], flush=True)
            page.screenshot(path="include_list.png")
            return

        download = info.value
        target = DOWNLOADS_DIR / download.suggested_filename
        download.save_as(target)
        print(f"Saved {target}", flush=True)
        self.close()


def accept_cookies(page: Page) -> None:
    """Click the cookie consent button if one appears."""
    button = page.get_by_role("button", name=COOKIE_BUTTON).first
    try:
        button.click(timeout=COOKIE_TIMEOUT)
    except PlaywrightTimeoutError:
        pass  # No banner this time


def get_bbo_session(
    existing_session: BboSession = None,
) -> BboSession:
    """Reuse the open session, or replace one you have closed."""
    session = existing_session
    if session is not None and not session.is_alive():
        session.close()  # Stops Playwright, so a new start() works
        session = None
    if session is None:
        session = BboSession()
    return session
