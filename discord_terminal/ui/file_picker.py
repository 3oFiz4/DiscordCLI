import tkinter
from pathlib import Path
from tkinter import filedialog


class FilePicker:
    def pick(self, title="Choose file to Upload. Any types.", filetypes=None):
        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        root.lift()
        root.focus_force()
        root.update()
        paths = filedialog.askopenfilenames(
            parent=root,
            title=title,
            filetypes=filetypes,
        )
        root.update()
        root.destroy()
        return [Path(path) for path in paths]
