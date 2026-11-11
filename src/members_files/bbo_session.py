import os
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import (
    Error as PlaywrightError,
)
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

from members_files.bbo_phoenix import BboPhoenixSession
from members_files.constants import DOWNLOADS_DIR

BBO_USERNAME = os.getenv("BBO_USERNAME")
BBO_PASSWORD = os.getenv("BBO_PASSWORD")

UPLOAD_ACTION = "add"
DOWNLOAD_ACTION = "dw"


class WebSessionError(Exception):
    """Exception raised for web session-related errors."""


@dataclass
class SessionConfig:
    date: str
    club_name: str
    club_id: str
    contact_name: str
    charge_rate: str


class BboSession(BboPhoenixSession):
    def __init__(self, headless: bool = False) -> None:
        super().__init__(headless=headless)

    def is_alive(self) -> bool:
        """True while the browser window is still open and responding."""
        try:
            self.page.evaluate("1")  # Raises if the window was closed
            return True
        except PlaywrightError:
            return False

    def download_include_list(self) -> None:
        """Download the include list from BBO."""
        page = self.page
        execute, frame, username, password = self._login_for_include_lists()
        frame.get_by_label("Action:").select_option(DOWNLOAD_ACTION)

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

    def upload_include_list(self, file_path: Path) -> None:
        """Upload `file_path` as the include list on BBO."""
        if not Path(file_path).exists():
            raise FileNotFoundError(file_path)

        page = self.page
        execute, frame, username, password = self._login_for_include_lists()
        frame.get_by_label("Action:").select_option(UPLOAD_ACTION)

        # The file box may only appear once the action is chosen
        file_input = frame.locator('input[type="file"]')
        try:
            file_input.wait_for(state="attached", timeout=5000)
        except PlaywrightTimeoutError:
            print("No file box on the form. It contains:", flush=True)
            for html in frame.locator("input, select").evaluate_all(
                "els => els.map(e => e.outerHTML.slice(0, 160))"
            ):
                print("  ", html, flush=True)
            page.screenshot(path="include_list.png")
            return
        file_input.set_input_files(file_path)

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
                return

        print("About to click Execute", flush=True)
        # A script click avoids the covering cell
        execute.evaluate("el => el.click()")

        page.wait_for_timeout(2000)
        print("BBO replied:", flush=True)
        print(frame.locator("body").inner_text()[:800], flush=True)
        self.close()

    def _login_for_include_lists(self) -> None:
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

        frame = self.page.locator("modal-content iframe").content_frame

        username = frame.get_by_role("textbox", name="Username:")
        password = frame.get_by_role("textbox", name="Password:")
        execute = frame.locator("#submit")
        username.wait_for(timeout=10000)

        # Type without clicking: a table cell covers the boxes
        username.press_sequentially(BBO_USERNAME, delay=30)
        password.press_sequentially(BBO_PASSWORD, delay=30)
        frame.get_by_label("Type:").select_option("include")
        return execute, frame, username, password


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
