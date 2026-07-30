import tkinter
from pathlib import Path
from tkinter import filedialog


class FilePicker:
    def pick(self, title="Choose file to Upload. Any types.", filetypes=None):
        try:
            root = tkinter.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            root.lift()
            root.focus_force()
            root.update()

            kwargs = {
                "parent": root,
                "title": title,
            }
            if filetypes is not None:
                kwargs["filetypes"] = filetypes

            paths = filedialog.askopenfilenames(**kwargs)
            root.update()
            root.destroy()

            if not paths:
                return []
            if isinstance(paths, str):
                return [Path(paths)]
            return [Path(path) for path in paths]
        except Exception:
            return []

