"""ReportFrame for Phoenix Members Files."""

import tkinter as tk
from tkinter import messagebox, ttk

from psiutils.constants import PAD
from psiutils.treeview import sort_treeview
from psiutils.utilities import restore_geometry, window_resize

from members_files.bbo_session import BboSession
from members_files.buttons import ButtonFrame, IconButton
from members_files.compare import Compare
from members_files.config import config
from members_files.constants import APP_TITLE
from members_files.state import state
from members_files.text import Text

txt = Text()

FRAME_TITLE = f"{APP_TITLE} - Reports"

FRAME_HEIGHT = 400

TREE_COLUMNS = (
    ("ebu", "EBU", 50),
    ("name", "Name", 100),
    ("username", "username", 50),
)


class ReportFrame:
    def __init__(self, parent: tk.Frame, paths: dict[str, str]) -> None:
        self.root = tk.Toplevel(parent.root)
        self.parent = parent
        self.paths = paths
        self.comparison = Compare(paths)
        self.comparison.compare()
        self.include_tree = None
        self.names_tree = None
        self.copy_include_button = None
        self.copy_bbo_button = None

        duplicates = ""
        if self.comparison.duplicates:
            bbo_file = self.paths["BBO names"]
            duplicates = f"Duplicates found in {bbo_file}"

        # tk variables
        self.duplicates = tk.StringVar(value=duplicates)

        self.show()

    def show(self) -> None:
        root = self.root
        restore_geometry(root, state, __file__)
        root.title(FRAME_TITLE)

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        self.main_frame = self._main_frame(root)
        self.main_frame.grid(
            row=0, column=0, sticky=tk.NSEW, padx=PAD, pady=PAD
        )

        self.button_frame = self._button_frame(root)
        self.button_frame.grid(
            row=1, column=0, sticky=tk.EW, padx=PAD, pady=PAD
        )

        if config.horizontal_sashes:
            for index, sash in enumerate(config.horizontal_sashes):
                self.main_frame.sash_place(index, 0, sash[1])

        sizegrip = ttk.Sizegrip(root)
        sizegrip.grid(sticky=tk.SE)

        root.update_idletasks()
        root.bind(
            "<Configure>",
            lambda e: window_resize(root, __file__, state),
        )

        root.bind("<Control-x>", self._dismiss)

    def _main_frame(self, master: tk.Frame) -> tk.PanedWindow:
        frame = tk.PanedWindow(master, orient=tk.VERTICAL)
        frame.columnconfigure(0, weight=1)

        include_frame = self._include_frame(frame)
        frame.add(include_frame, height=FRAME_HEIGHT)

        bbo_frame = self._bbo_frame(frame)
        frame.add(bbo_frame, height=FRAME_HEIGHT)

        duplicate_frame = self._duplicate_frame(frame)
        frame.add(duplicate_frame)

        return frame

    def _include_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ttk.Frame(master)
        frame.columnconfigure(0, weight=1)

        row = 0
        label = ttk.Label(frame, text="Members missing from include")
        label.grid(row=row, column=0, sticky=tk.W, padx=PAD, pady=PAD)

        row += 1
        frame.rowconfigure(row, weight=1)
        self.include_tree = self._get_include_tree(frame)
        self.include_tree.grid(row=row, column=0, sticky=tk.NSEW)

        self.copy_include_button = IconButton(
            frame, txt.COPY, "copy-clipboard", self._copy_include, True
        )
        self.copy_include_button.grid(row=row, column=1, padx=PAD, sticky=tk.N)

        upload_button = IconButton(
            frame, txt.UPLOAD, "upload", self._upload_include
        )
        upload_button.grid(row=row, column=2, padx=PAD, sticky=tk.N)

        self.copy_include_button.disable()
        self._populate_include_tree()
        return frame

    def _bbo_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ttk.Frame(master)
        frame.columnconfigure(0, weight=1)

        row = 0
        label = ttk.Label(frame, text="Members missing from bbo_names")
        label.grid(row=row, column=0, sticky=tk.W, padx=PAD, pady=PAD)

        row += 1
        frame.rowconfigure(row, weight=1)
        self.names_tree = self._get_names_tree(frame)
        self.names_tree.grid(row=row, column=0, sticky=tk.NSEW)

        self.copy_bbo_button = IconButton(
            frame, txt.COPY, "copy-clipboard", self._copy_names, True
        )
        self.copy_bbo_button.grid(row=row, column=1, padx=PAD, sticky=tk.N)
        self.copy_bbo_button.disable()
        self._populate_names_tree()
        return frame

    def _duplicate_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ttk.Frame(master)
        frame.columnconfigure(0, weight=1)

        row = 0
        label = ttk.Label(frame, text="Members duplicated in bbo_names")
        label.grid(row=row, column=0, sticky=tk.W, padx=PAD, pady=PAD)

        row += 1
        frame.rowconfigure(row, weight=1)
        self.duplicate_tree = self._get_duplicate_tree(frame)
        self.duplicate_tree.grid(row=row, column=0, sticky=tk.NSEW)

        self.copy_duplicate_button = IconButton(
            frame, txt.COPY, "copy-clipboard", self._copy_duplicate, True
        )
        self.copy_duplicate_button.grid(
            row=row, column=1, padx=PAD, sticky=tk.N
        )
        self.copy_duplicate_button.disable()
        self._populate_duplicate_tree()
        return frame

    def _button_frame(self, master: tk.Frame) -> tk.Frame:
        frame = ButtonFrame(master, tk.HORIZONTAL)
        frame.buttons = self._frame_buttons(frame)
        frame.enable(False)
        return frame

    def _frame_buttons(self, frame: ButtonFrame) -> tk.Frame:
        return [
            frame.icon_button("cancel", self._dismiss, tag="exit"),
        ]

    def _get_include_tree(self, master: tk.Frame) -> ttk.Treeview:
        """Return  a tree widget."""
        tree = ttk.Treeview(
            master,
            selectmode="browse",
            height=15,
            show="headings",
        )

        col_list = tuple(col[0] for col in TREE_COLUMNS)

        tree["columns"] = col_list
        for col in TREE_COLUMNS:
            (col_key, col_text, col_width) = (col[0], col[1], col[2])
            tree.heading(
                col_key,
                text=col_text,
                command=lambda c=col_key: sort_treeview(tree, c, False),
            )
            tree.column(col_key, width=col_width, anchor=tk.W)
        return tree

    def _populate_include_tree(self) -> None:

        self.include_tree.delete(*self.include_tree.get_children())
        if len(self.comparison.missing_from_include) > 0:
            self.copy_include_button.enable()
        else:
            values = ("", "No names missing", "")
            self.include_tree.insert("", "end", values=values)

        missing = dict(
            sorted(
                self.comparison.missing_from_include.items(),
                key=lambda item: item[1].bbo,
            )
        )
        for item in missing.values():
            values = (
                item.ebu,
                f"{item.first_name} {item.last_name}",
                item.bbo,
            )
            self.include_tree.insert("", "end", values=values)

    def _copy_include(self, *args):
        dlg = messagebox.askyesno(
            "", "Overwrite include file?", parent=self.root
        )
        if not dlg:
            return

        self.comparison.create_include_from_members()
        self.comparison.compare()
        self._populate_include_tree()

    def _get_names_tree(self, master: tk.Frame) -> ttk.Treeview:
        """Return  a tree widget."""
        tree = ttk.Treeview(
            master,
            selectmode="browse",
            height=15,
            show="headings",
        )

        col_list = tuple(col[0] for col in TREE_COLUMNS)

        tree["columns"] = col_list
        for col in TREE_COLUMNS:
            (col_key, col_text, col_width) = (col[0], col[1], col[2])
            tree.heading(
                col_key,
                text=col_text,
                command=lambda c=col_key: sort_treeview(tree, c, False),
            )
            tree.column(col_key, width=col_width, anchor=tk.W)
        return tree

    def _populate_names_tree(self) -> None:
        self.names_tree.delete(*self.names_tree.get_children())
        if len(self.comparison.missing_from_bbo) > 0:
            self.copy_bbo_button.enable()
        else:
            values = ("", "No names missing", "")
            self.names_tree.insert("", "end", values=values)
        for item in self.comparison.missing_from_bbo.values():
            values = (
                item.ebu,
                f"{item.first_name} {item.last_name}",
                item.bbo,
            )
            self.names_tree.insert("", "end", values=values)

    def _copy_names(self, *args):
        dlg = messagebox.askyesno("", "Overwrite bbo_names file?")
        if not dlg:
            return

        combined = {
            **self.comparison.missing_from_bbo,
            **self.comparison.members_bbo,
        }
        names = [
            (
                f"{member.bbo},"
                f"{member.first_name},"
                f"{member.last_name},"
                f"{member.ebu}"
            )
            for member in combined.values()
        ]

        path = self.paths["BBO names"]
        with open(path, "w", encoding="utf8") as f_include:
            f_include.write("\n".join(sorted(names)))
        self.comparison.compare()
        self._populate_names_tree()

    def _get_duplicate_tree(self, master: tk.Frame) -> ttk.Treeview:
        """Return a tree widget."""
        tree = ttk.Treeview(
            master,
            height=15,
            show="headings",
        )

        col_list = tuple(col[0] for col in TREE_COLUMNS)

        tree["columns"] = col_list
        for col in TREE_COLUMNS:
            (col_key, col_text, col_width) = (col[0], col[1], col[2])
            tree.heading(
                col_key,
                text=col_text,
                command=lambda c=col_key: sort_treeview(tree, c, False),
            )
            tree.column(col_key, width=col_width, anchor=tk.W)
        return tree

    def _populate_duplicate_tree(self) -> None:
        self.duplicate_tree.delete(*self.duplicate_tree.get_children())
        if len(self.comparison.duplicates) > 0:
            # self.copy_duplicate_button.enable()
            pass
        else:
            values = ("", "No duplicates found", "")
            self.duplicate_tree.insert("", "end", values=values)
        for item in self.comparison.duplicates.values():
            values = (
                item.ebu,
                f"{item.first_name} {item.last_name}",
                item.bbo,
            )
            self.duplicate_tree.insert("", "end", values=values)

    def _copy_duplicate(self, *args):
        # dlg = messagebox.askyesno(
        #     '',
        #     'Overwrite bbo_names file?'
        # )
        # if not dlg:
        #     return

        # combined = {
        #     **self.comparison.duplicates,
        #     **self.comparison.members_bbo
        #     }
        # names = [(f'{member.bbo},'
        #           f'{member.first_name},'
        #           f'{member.last_name},'
        #           f'{member.ebu}')
        #          for member in combined.values()]

        # path = self.parent.bbo_names_file.get()
        # with open(path, 'w', encoding='utf8') as f_include:
        #     f_include.write('\n'.join(sorted(names)))
        # self.comparison = Compare(self.parent)
        # self._populate_duplicate_tree()
        pass

    def _upload_include(self, *args) -> None:
        bbo = BboSession()
        bbo.upload_include_list(self.paths["BBO include"])
        self.parent.root.destroy()

    def _save_sashes(self) -> None:
        horizontal_sashes = [
            self.main_frame.sash_coord(index)
            for index in range(len(config.horizontal_sashes))
        ]
        config.update("horizontal_sashes", horizontal_sashes)
        config.save()

    def _dismiss(self, *args) -> None:
        self._save_sashes()
        self.root.destroy()
