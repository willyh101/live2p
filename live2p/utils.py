"""
Generic utilities for online analysis.
"""

import asyncio
import functools
import logging
import os
from pathlib import Path
import time
from datetime import datetime
from glob import glob
import json
import warnings

import numpy as np
import pandas as pd
import scipy.io as sio
from ScanImageTiffReader import ScanImageTiffReader

with warnings.catch_warnings():
    warnings.simplefilter('ignore', category=FutureWarning)
    import caiman as cm

logger = logging.getLogger('live2p')

def mm3d_to_img(path, chan=0):
    """
    Gets the img data from a makeMasks3D file and flips it into a (512,512,z-depth) ndarray.

    Args:
        path (str): location of matlab file
        chan (int, optional): RGB channel to index into. Defaults to 0 (aka 'red').

    Returns:
        ndarray: (512,512,z-depth) image
    """
    mat = sio.loadmat(path)
    img = mat['img'].squeeze()

    img = np.array([i[:,:,chan] for i in img])

    return img

def load_sources(path):
    mat = sio.loadmat(path)
    srcs = mat['sources'].squeeze()
    srcs = np.array([i.max(2) for i in srcs])
    return srcs

def make_ain(path, plane, left_crop, right_crop):
    mat = sio.loadmat(path)
    srcs = mat['sources'].squeeze()
    
    srcs = srcs[plane]
    srcs = srcs[:, left_crop:right_crop, :]
    
    A = np.zeros((np.prod(srcs.shape[:2]), srcs.shape[2]), dtype=bool)
    
    for i in range(srcs.shape[2]):
        A[:,i] = srcs[:,:,i].flatten('F')
        
    print(f'Plane {plane}: Found {srcs.shape[2]} sources from MM3D...')
        
    return A
    
def remove_artifacts(img, left_crop, right_crop):
    """
    Clips off the stim laser artifacts from the mean tiff.

    Args:
        img (array): n,512,512 image where n is planes
    """
    
    return img[:, :, left_crop:right_crop]

def tic():
    """Records the time in highest resolution possible for timing code."""
    return time.perf_counter()

def toc(tic):
    """Returns the time since 'tic' was called."""
    return time.perf_counter() - tic

def ptoc(tic, start_string='Time elapsed:', end_string='s'):
    """
    Print a default or custom print statement with elapsed time. Both the start_string
    and end_string can be customized. Autoformats with single space between start, time, 
    stop. Returns the time elapsed.

    Format -> 'start_string' + 'elapsed time in seconds' + 'end_string'.
    Default -> start_string = 'Time elapsed:', end_string = 's'.
    """
    t = toc(tic)
    pstring = ' '.join([start_string, f'{t:.4f}', end_string])
    print(pstring)
    return t

def cleanup(folder, filetype, verbose=True):
    files = glob(folder + '*.' + filetype)
    if files:
        for f in files:
            os.remove(f)
            if verbose:
                print('Removed ' + f)
    else:
        if verbose:
            print('Nothing to remove!')

def slice_movie(mov_path, x_slice, y_slice, t_slice):
    with ScanImageTiffReader(mov_path) as reader:
        data = reader.data()
        data = data[t_slice, y_slice, x_slice]
    return data

def tiffs2array(movie_list, x_slice, y_slice, t_slice):
    data = [slice_movie(str(mov), x_slice, y_slice, t_slice) for mov in movie_list]
    return np.concatenate(data)

def get_tiff_lengths(movie_list, x_slice, y_slice, t_slice):
    data = [slice_movie(str(mov), x_slice, y_slice, t_slice).shape[0] for mov in movie_list]
    return np.concatenate(data)
            
def get_nchannels(file):
    with ScanImageTiffReader(file) as reader:
        metadata = reader.metadata()
    channel_pass_1 = metadata.split('channelSave = [')
    if len(channel_pass_1)==1:
        nchannels = 1
    else:
        nchannels = len(metadata.split('channelSave = [')[1].split(']')[0].split(';'))
    return nchannels

def get_nvols(file):
    with ScanImageTiffReader(file) as reader:
        metadata = reader.metadata()
    if metadata.split('hStackManager.zs = ')[1][0]=='0':
        return 1
    nvols = len(metadata.split('hStackManager.zs = [')[1].split(']')[0].split(' '))
    return nvols

def random_view(arr, length, n=1):
    """
    Generates a random view from an (1D) array without shuffling any of the data.

    Args:
        arr (np.array): array to use
        length (int): length of slice to take
        n (int): number of slices to return
        
    Returns:
        random views into array arr.
    """
    assert arr.ndim == 1, 'Must pass 1D array.'
    
    out = []
    for i in range(n):
    # choose random starting point
        start_idx = np.random.randint(arr.size - length)
        rand_slice = arr[start_idx:start_idx + length]
        out.append(rand_slice)
    
    return np.array(out)
    
def format_json(**kwargs):
    for kw, val in kwargs.items():
        if isinstance(val, list) or isinstance(val, dict):
            continue
        elif isinstance(val, np.ndarray):
            kwargs[kw] = val.tolist()
        elif isinstance(val, pd.DataFrame):
            kwargs[kw] = val.to_json()
        else:
            logger.error(f'Failed to make {kw} of type {type(val)} json compatible.')
            raise NotImplementedError(f'Failed to make {kw} of type {type(val)} json compatible.')  
    return kwargs

def now():
    rn = datetime.now()
    return rn.strftime('%H:%M:%S')

def load_json(path):
    with open(path, 'r') as file:
        data_json = json.load(file)
    return data_json

def load_as_obj(caiman_data_path):
    """hdf5 -> caiman object"""
    return cm.source_extraction.cnmf.cnmf.load_CNMF(caiman_data_path)

def get_tslice(z_idx, ch_idx, nchannels, nplanes):
    return slice((z_idx*nchannels)+ch_idx, -1, nplanes*nchannels)

def get_true_mm3d_range(path, buffer=0):
    mat = sio.loadmat(path)
    sources = np.concatenate(mat['sources'].squeeze(), axis=2)
    vals = np.argwhere(sources)[:,1]
    return vals.min()-buffer, vals.max()+buffer

def find_mm3d(folder):
    expected_path = Path(folder,'makeMasks3D_img.mat')
    if expected_path.exists():
        return str(expected_path)
    else:
        raise FileNotFoundError(f'makeMasks3D_img not found in this folder: {expected_path.parent}')
    
def tictoc(func):
    """Prints the runtime of the decorated function."""
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        logger.info(f'<{func.__module__}.{func.__name__}> done in {run_time:.3f}s')
        return value
    return wrapper_timer

def run_in_executor(func):
    """Runs a blocking operation from a seperate thread."""
    @functools.wraps(func)
    def wrapper_run_in_executor(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper_run_in_executor