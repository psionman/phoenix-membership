"""Constants for Phoenix Members Files."""

from pathlib import Path

from platformdirs import (
    user_config_dir,
    user_data_dir,
    user_downloads_dir,
    user_state_dir,
)
from psiutils.known_paths import resolve_path

from members_files import __app_name__, __author__

# General
AUTHOR = "Jeff Watkins"
APP_NAME = "phoenix_members"
APP_AUTHOR = "psionman"
HTML_DIR = resolve_path("html", __file__)
HELP_URI = ""

# Paths
CONFIG_PATH = Path(user_config_dir(APP_NAME, APP_AUTHOR), "config.toml")
USER_DATA_DIR = user_data_dir(APP_NAME, APP_AUTHOR)
USER_DATA_FILE = "members.json"
HOME = str(Path.home())
STATE_DIR = user_state_dir(__app_name__, __author__)
DOWNLOADS_DIR = Path(user_downloads_dir())


# Buttons and text
PSIUTILS_DIR = user_data_dir("psiutils", __author__)
BUTTONS_DIR = Path(PSIUTILS_DIR, "buttons")
BUTTON_ICON_PATH = str(Path(BUTTONS_DIR, "icons"))
BUTTON_CONFIG_PATH = str(Path(BUTTONS_DIR, "buttons.json"))
TEXT_FILE = Path(PSIUTILS_DIR, "text", "text.json")

# GUI
APP_TITLE = "Phoenix Members Files"
ICON_FILE = resolve_path(Path("images", "icon.png"), __file__)
DEFAULT_GEOMETRY = "400x500"
