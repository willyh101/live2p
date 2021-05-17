import numpy as np
import warnings

with warnings.catch_warnings():
    warnings.simplefilter('ignore', category=FutureWarning)
    import caiman as cm

def make_images(caiman_obj):
    Yr, dims, T = cm.load_memmap(caiman_obj.mmap_file)
    return np.reshape(Yr, [T] + list(dims), order='F')

def find_com(A, dims, x_1stPix):
    XYcoords= cm.base.rois.com(A, *dims)
    XYcoords[:,1] = XYcoords[:,1] + x_1stPix #add the dX from the cut FOV
    i = [1, 0]
    return XYcoords[:,i] #swap them