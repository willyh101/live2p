from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilename, askopenfilenames

def openfoldergui(rootdir=None, title=None):
    return _get_opengui(askdirectory, initialdir=rootdir, title=title)

def openfilegui(rootdir=None, title=None):
    return _get_opengui(askopenfilename, initialdir=rootdir, title=title)

def openfilesgui(rootdir=None, title=None):
    return _get_opengui(askopenfilenames,initialdir=rootdir, title=title)

def _get_opengui(openfun, *args, **kwargs):
    root = Tk()
    root.lift()
    root.attributes("-topmost", True)
    root.withdraw()
    dirname = openfun(parent=root, *args, **kwargs)
    root.destroy()
    return dirname