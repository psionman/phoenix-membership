# forms/frm_config.py
"""ConfigFrame for members_files."""

import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from psiutils.constants import PAD, FileTypes
from psiutils.utilities import restore_geometry, window_resize

from members_files import logger
from members_files.buttons import ButtonFrame, IconButton
from members_files.config import FIELDS, config, save_config
from members_files.constants import APP_TITLE, DEFAULT_GEOMETRY, DOWNLOADS_DIR
from members_files.state import state
from members_files.text import Text

txt = Text()


class ConfigFrame:
    """
    A configuration dialog for editing application settings.
    """

    def __init__(self, parent: tk.Frame) -> None:
        self.root = tk.Toplevel(parent.root)
        self.parent = parent
        self.dialog_opened = False
        self.save_button = None

        # Assign tk variables and check for changes
        config.assign_tk_variables(self, FIELDS, self._check_value_changed)

        self._show()

    def _show(self) -> None:
        """
        Initialize and display the configuration form GUI.
        """
        root = self.root
        restore_geometry(root, state, __file__, default=DEFAULT_GEOMETRY)
        root.transient(self.parent.root)
        root.title(f"{APP_TITLE} - {txt.CONFIG}")

        root.bind("<Control-x>", self._dismiss)
        root.bind("<Control-s>", self._save_config)
        root.bind(
            "<Configure>",
            lambda e: window_resize(root, __file__, state),
        )

        # root.bind("<FocusIn>", self._set_config)

        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)

        main_frame = self._main_frame(root)
        main_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=PAD, pady=PAD)
        self.button_frame = self._button_frame(root)
        self.button_frame.grid(
            row=8, column=0, columnspan=9, sticky=tk.EW, padx=PAD, pady=PAD
        )

        sizegrip = ttk.Sizegrip(root)
        sizegrip.grid(sticky=tk.SE)

    def _main_frame(self, master: tk.Frame) -> ttk.Frame:
        """
        Create and return the main frame containing form input widgets.
        """
        frame = ttk.Frame(master)
        frame.columnconfigure(1, weight=1)

        row = 0
        label = ttk.Label(frame, text="Members File")
        label.grid(row=row, column=0, sticky=tk.E, padx=PAD, pady=PAD)

        entry = ttk.Entry(frame, textvariable=self.members_file)
        entry.grid(row=row, column=1, sticky=tk.EW)

        button = IconButton(
            frame, txt.BROWSE, "file-find-outline", self._get_members_file
        )
        button.grid(row=row, column=2, padx=PAD, pady=PAD)

        row += 1
        label = ttk.Label(frame, text="Include File")
        label.grid(row=row, column=0, sticky=tk.E, padx=PAD)

        entry = ttk.Entry(frame, textvariable=self.include_list_file)
        entry.grid(row=row, column=1, sticky=tk.EW)

        button = IconButton(
            frame, txt.BROWSE, "file-find-outline", self._get_include_file
        )
        button.grid(row=row, column=2, padx=PAD, pady=PAD)

        row += 1
        label = ttk.Label(frame, text="BBO names file")
        label.grid(row=row, column=0, sticky=tk.E, padx=PAD)

        entry = ttk.Entry(frame, textvariable=self.bbo_names_file)
        entry.grid(row=row, column=1, sticky=tk.EW)

        button = IconButton(
            frame, txt.BROWSE, "file-find-outline", self._get_bbo_names_file
        )
        button.grid(row=row, column=2, padx=PAD, pady=PAD)

        return frame

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.HORIZONTAL)
        frame.buttons = self._frame_buttons(frame)
        self.save_button = frame.get_button("save")
        frame.disable()
        return frame

    def _frame_buttons(self, frame: ButtonFrame) -> list[IconButton]:
        return [
            frame.icon_button("save", self._save_config, True, tag="save"),
            frame.icon_button("exit", self._dismiss),
        ]

    def _check_value_changed(self, *args) -> bool:
        """
        Enable or disable form buttons based on changes in configuration.
        """
        enable = bool(self._config_changes())
        self.button_frame.enable(enable)

    def _get_members_file(self, *args) -> None:
        if self.members_file.get():
            initialdir = Path(self.members_file.get()).parent
        else:
            initialdir = DOWNLOADS_DIR
        path = filedialog.askopenfilename(
            initialdir=initialdir,
            parent=self.root,
            filetypes=FileTypes.CSV.value,
        )
        if path:
            template = re.sub(r"\d{8}", "YYYYMMDD", path)
            self.members_file.set(template)

    def _get_include_file(self, *args) -> None:
        if self.include_list_file.get():
            initialdir = Path(self.include_list_file.get()).parent
        else:
            initialdir = DOWNLOADS_DIR
        path = filedialog.askopenfilename(
            initialdir=initialdir,
            parent=self.root,
            filetypes=FileTypes.TXT.value,
        )
        if path:
            self.include_list_file.set(path)

    def _get_bbo_names_file(self, *args) -> None:
        if self.bbo_names_file.get():
            initialdir = Path(self.bbo_names_file.get()).parent
        else:
            initialdir = DOWNLOADS_DIR
        path = filedialog.askopenfilename(
            initialdir=initialdir,
            parent=self.root,
            filetypes=FileTypes.TXT.value,
        )
        if path:
            self.bbo_names_file.set(path)

    def _get_directory(self, default: str) -> str:
        """
        Prompt the user to select a new data directory and update the value.
        """
        self.dialog_opened = True
        return filedialog.askdirectory(
            initialdir=Path(default),
            parent=self.root,
        )

    def _save_config(self):
        changes = {
            field: f"(old value={change[0]}, new_value={change[1]})"
            for field, change in self._config_changes().items()
        }

        for field in FIELDS:
            config.update(field, getattr(self, field).get())

        save_config(config)
        logger.info("Config saved", changes=changes)
        self.save_button.disable()
        self._dismiss()

    def _config_changes(self) -> dict:
        stored = config.config
        return {
            field: (stored[field], getattr(self, field).get())
            for field in FIELDS
            if stored[field] != getattr(self, field).get()
        }

    def _set_config(self, *args) -> None:
        if self.dialog_opened:
            self.dialog_opened = False
            return
        for field in FIELDS:
            getattr(self, field).set(config.config[field])

    def _dismiss(self, *args) -> None:
        """
        Close the configuration window and terminate the application.
        """
        self.root.grab_release()
        self.root.destroy()
