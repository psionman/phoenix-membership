# state.py
import tomllib
from pathlib import Path

import tomli_w

from members_files.constants import STATE_DIR

DEFAULT_GEOMETRY = {
    "frm_main": "1400x600",
    "frm_config": "800x200",
    "frm_email": "700x900",
}


class State:
    def __init__(self):
        self.geometry: dict[str, str] = {}
        self.horizontal_sashes: list[tuple[int, int]] = [[], []]

        self.get_state()

    def get_state(self) -> Path:
        state_file = Path(STATE_DIR, "state.toml")
        try:
            with open(state_file, "rb") as f:
                data = tomllib.load(f)
        except FileNotFoundError:
            data = {}
        self.geometry = data.get("geometry", DEFAULT_GEOMETRY)
        if not self.geometry:
            self.geometry = DEFAULT_GEOMETRY
        self.horizontal_sashes = data.get("horizontal_sashes", [[], []])

    def serialize(self):
        return {
            "geometry": self.geometry,
            "horizontal_sashes": self.horizontal_sashes,
        }

    def save(self):
        data = self.serialize()
        state_file = Path(STATE_DIR, "state.toml")
        if not state_file.parent.exists():
            state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, "wb") as f:
            tomli_w.dump(data, f)

    def update(self, key: str, value: any):
        self.__dict__[key] = value
        self.save()


state = State()
