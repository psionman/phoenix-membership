"""MainFrame for Phoenix Members Files."""

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from psiutils.constants import (
    CSV_FILE_TYPES,
    DOWNLOADS_DIR,
    PAD,
    TXT_FILE_TYPES,
    Pad,
)
from psiutils.utilities import restore_geometry, window_resize

from members_files.bbo_session import get_bbo_session
from members_files.bridgewebs_session import get_bridgewebs_session
from members_files.buttons import ButtonFrame, IconButton
from members_files.config import config
from members_files.constants import APP_TITLE
from members_files.forms.frm_report import ReportFrame
from members_files.main_menu import MainMenu
from members_files.state import state
from members_files.text import Text

txt = Text()
FRAME_TITLE = APP_TITLE


class AppFrame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root

        members_file = config.members_file
        members_file = members_file.replace(
            "YYYYMMDD", datetime.now().strftime("%Y%m%d")
        )

        bbo_names_file = config.bbo_names_file
        include_list_file = config.include_list_file

        # tk variables
        self.members_file = tk.StringVar(value=members_file)
        self.include_list_file = tk.StringVar(value=include_list_file)
        self.bbo_names_file = tk.StringVar(value=bbo_names_file)

        self._show()
        # TODO: Remove this when we have a proper login system
        # self._download_member_file()
        # self._download_include_file()

    def _show(self):
        root = self.root
        restore_geometry(root, state, __file__)
        root.title(FRAME_TITLE)

        main_menu = MainMenu(self)
        main_menu.create()

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        row = 0
        main_frame = self._main_frame(root)
        main_frame.grid(row=row, column=0, sticky=tk.NSEW, padx=PAD, pady=PAD)

        row += 1
        self.button_frame = self._button_frame(root)
        self.button_frame.grid(
            row=1, column=0, sticky=tk.EW, padx=PAD, pady=PAD
        )

        sizegrip = ttk.Sizegrip(root)
        sizegrip.grid(sticky=tk.SE)

        root.update_idletasks()
        root.bind("<Control-x>", self._dismiss)
        root.bind("<Control-o>", self._process)
        root.bind(
            "<Configure>",
            lambda event, arg=None: window_resize(root, __file__, state),
        )

    def _main_frame(self, master: tk.Frame) -> ttk.Frame:
        frame = ttk.Frame(master)
        frame.columnconfigure(1, weight=1)

        row = 0
        label = ttk.Label(frame, text="Membership file")
        label.grid(row=row, column=0, sticky=tk.E, padx=PAD, pady=PAD)

        entry = ttk.Entry(frame, textvariable=self.members_file)
        entry.grid(row=row, column=1, sticky=tk.EW)

        button = IconButton(
            frame, txt.BROWSE, "file-find-outline", self._get_member_file
        )
        button.grid(row=row, column=2, padx=PAD, pady=Pad.S)

        button = IconButton(
            frame, txt.DOWNLOAD, "download", self._download_member_file
        )
        button.grid(row=row, column=3, padx=PAD, pady=Pad.S)

        row += 1
        label = ttk.Label(frame, text="BBO include file")
        label.grid(row=row, column=0, sticky=tk.E, padx=PAD, pady=PAD)

        entry = ttk.Entry(frame, textvariable=self.include_list_file)
        entry.grid(row=row, column=1, sticky=tk.EW)

        button = IconButton(
            frame, txt.BROWSE, "file-find-outline", self._get_bbo_include_file
        )
        button.grid(row=row, column=2, padx=PAD, pady=Pad.S)

        button = IconButton(
            frame, txt.DOWNLOAD, "download", self._download_include_file
        )
        button.grid(row=row, column=3, padx=PAD, pady=Pad.S)

        row += 1
        label = ttk.Label(frame, text="BBO names file")
        label.grid(row=row, column=0, sticky=tk.E, padx=PAD, pady=PAD)

        entry = ttk.Entry(frame, textvariable=self.bbo_names_file)
        entry.grid(row=row, column=1, sticky=tk.EW)

        button = IconButton(
            frame, txt.BROWSE, "file-find-outline", self._get_bbo_names_file
        )
        button.grid(row=row, column=2, padx=PAD, pady=Pad.S)

        return frame

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.HORIZONTAL)
        frame.buttons = self._frame_buttons(frame)
        frame.enable(False)
        return frame

    def _frame_buttons(self, frame: ButtonFrame) -> list[IconButton]:
        return [
            frame.icon_button("report", self._process),
            frame.icon_button("cancel", self._dismiss),
        ]

    def _get_member_file(self, *args) -> None:
        initialfile = self.members_file.get()
        initialdir = DOWNLOADS_DIR
        if initialfile:
            initialdir = Path(initialfile).parent
        members_file = filedialog.askopenfilename(
            initialdir=initialdir,
            initialfile=initialfile,
            filetypes=CSV_FILE_TYPES,
        )
        if members_file:
            self.members_file.set(members_file)
            self.data_file.content["members_file"] = members_file
            self.data_file.write()

    def _get_bbo_include_file(self, *args) -> None:
        initialfile = self.include_list_file.get()
        initialdir = DOWNLOADS_DIR
        if initialfile:
            initialdir = Path(initialfile).parent
        include_list_file = filedialog.askopenfilename(
            initialdir=initialdir,
            initialfile=initialfile,
            filetypes=TXT_FILE_TYPES,
        )
        if include_list_file:
            self.include_list_file.set(include_list_file)
            self.data_file.content["include_list_file"] = include_list_file
            self.data_file.write()

    def _get_bbo_names_file(self, *args) -> None:
        initialfile = self.bbo_names_file.get()
        initialdir = DOWNLOADS_DIR
        if initialfile:
            initialdir = Path(initialfile).parent
        bbo_names_file = filedialog.askopenfilename(
            initialdir=initialdir,
            initialfile=initialfile,
            filetypes=TXT_FILE_TYPES,
        )
        if bbo_names_file:
            self.bbo_names_file.set(bbo_names_file)
            self.data_file.content["bbo_names_file"] = bbo_names_file
            self.data_file.write()

    def _process(self, *args) -> None:
        paths = {
            "Membership": self.members_file.get(),
            "BBO include": self.include_list_file.get(),
            "BBO names": self.bbo_names_file.get(),
        }
        for key, path in paths.items():
            if not Path(path).exists():
                messagebox.showerror("Error", f"{key} file not found")
                return
        dlg = ReportFrame(self, paths)
        self.root.wait_window(dlg.root)

    def _download_member_file(self, *args) -> None:
        session = get_bridgewebs_session()
        session.download_members_file()

    def _download_include_file(self, *args) -> None:
        session = get_bbo_session()
        session.download_include_list()

    def _dismiss(self, *args) -> None:
        self.root.destroy()
