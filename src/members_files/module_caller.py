"""Module caller for Phoenix Members Files."""

import tkinter as tk

from data_files import DataFile
from psiutils.module_caller import ModuleCaller as ModuleCallerBase

from members_files.forms.frm_config import ConfigFrame
from members_files.forms.frm_report import ReportFrame


class ModuleCaller(ModuleCallerBase):
    def __init__(self, root, parsed_args: dict) -> None:
        self.modules = {
            "config": (self._config, None),
            "report": (self._report, None),
        }
        super().__init__(root, parsed_args)

    def _config(self) -> None:
        """
        Open the configuration dialog and wait until it is closed.

        Creates an instance of ConfigFrame and waits for its window to close
        before continuing.
        """
        dlg = ConfigFrame(self)
        self.root.wait_window(dlg.root)

    def _report(self) -> None:
        """
        Open the configuration dialog and wait until it is closed.

        Creates an instance of ConfigFrame and waits for its window to close
        before continuing.
        """
        self.data_file = DataFile()
        self.data_file.read()

        member_file = ""
        bbo_include_file = ""
        bbo_names_file = ""
        if "member_file" in self.data_file.content:
            member_file = self.data_file.content["member_file"]
        if "bbo_include_file" in self.data_file.content:
            bbo_include_file = self.data_file.content["bbo_include_file"]
        if "bbo_names_file" in self.data_file.content:
            bbo_names_file = self.data_file.content["bbo_names_file"]

        self.member_file = tk.StringVar(value=member_file)
        self.bbo_include_file = tk.StringVar(value=bbo_include_file)
        self.bbo_names_file = tk.StringVar(value=bbo_names_file)
        dlg = ReportFrame(self)
        self.root.wait_window(dlg.root)
