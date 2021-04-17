from tkinter import Tk, filedialog

def openfoldergui(rootdir=None, title=None):
    root = Tk()
    root.lift()
    root.attributes("-topmost", True)
    root.withdraw()
    dirname = filedialog.askdirectory(parent=root, initialdir=rootdir,
                                      title=title)
    return dirname

def openfilegui(rootdir=None, title=None):
    root = Tk()
    root.lift()
    root.attributes("-topmost", True)
    root.withdraw()
    dirname = filedialog.askopenfilename(parent=root, initialdir=rootdir,
                                         title=title)
    return dirname

def openfilesgui(rootdir=None, title=None):
    root = Tk()
    root.lift()
    root.attributes("-topmost", True)
    root.withdraw()
    dirname = filedialog.askopenfilenames(parent=root, initialdir=rootdir,
                                         title=title)
    return dirname