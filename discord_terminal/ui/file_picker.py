import tkinter
from pathlib import Path
from tkinter import filedialog


class FilePicker:
    def pick(self):
        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        root.lift()
        root.focus_force()
        root.update()
        paths = filedialog.askopenfilenames(
            parent=root,
            title="Choose file to Upload. Any types.",
        )
        root.update()
        root.destroy()
        return [Path(path) for path in paths]
