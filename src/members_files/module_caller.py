"""Module caller for Phoenix Members Files."""

from datetime import datetime

from data_files import DataFile
from psiutils.module_caller import ModuleCaller as ModuleCallerBase

from members_files.config import config
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

        members_file = config.members_file
        members_file = members_file.replace(
            "YYYYMMDD", datetime.now().strftime("%Y%m%d")
        )

        bbo_names_file = config.bbo_names_file
        include_list_file = config.include_list_file

        paths = {
            "Membership": members_file,
            "BBO include": include_list_file,
            "BBO names": bbo_names_file,
        }
        dlg = ReportFrame(self, paths)
        self.root.wait_window(dlg.root)
