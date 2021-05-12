"""Backend for handling online analysis of data from caiman."""
# TODO: possibly split this up into data processing and generic stuff?

import warnings

import numpy as np
import pandas as pd
import scipy.stats as stats
import sklearn

from .utils import load_json, load_as_obj

with warnings.catch_warnings():
    warnings.simplefilter('ignore', category=FutureWarning)
    import caiman as cm
    
def process_data(c, splits, fr, stim_times=None, normalizer='scale', align_to=1, total_length=4):
    
    traces, trialwise_data = clean_data(c, splits, normalizer=normalizer)
    
    # convert seconds to frames
    align_to *= int(fr)
    total_length *= int(fr)
    baseline_length = align_to - 1
    
    if stim_times is not None:
        stim_times *= int(fr)
        trialwise_data = do_stimalign(trialwise_data, stim_times, align_to)
        
    trialwise_data = baseline_subtract(trialwise_data, baseline_length)
    psths = cut_psths(trialwise_data, length=total_length)
    
    return traces, psths
    
def clean_data(c, trial_lengths, normalizer='scale'):
    """Min subtract, normalize, and make trialwise."""
    
    data  =  np.asarray(c)
    # min subtract and normalize
    data = min_subtract(data)
    
    norm_routines = {
        'none': data, # nothing done...
        'minmax': sklearn.preprocessing.minmax_scale(data, axis=1), # scaled to min max (not abs)
        'zscore': stats.zscore(data, axis=1), # old fashion zscoring
        'norm': sklearn.preprocessing.normalize(data, axis=1), # L2 norm
        'scale': sklearn.preprocessing.scale(data, axis=1), # mean subtracted, divided by standard dev
    }
        
    normed_data = norm_routines[normalizer]
        
    traces = make_trialwise(normed_data, trial_lengths)
    
    return normed_data, traces

def do_stimalign(traces, stim_times, align_to):
    # FIXME: URGENT
    # ! this isn't correct actually because to stim align by trials you still need a list
    if isinstance(stim_times, int):
        traces = stim_align_all_cells(traces, stim_times, align_to)
    
    elif len(stim_times) > 1:
        try:
            assert len(stim_times) == traces.shape[0] # must have same length/size as the number of cells
            traces = stim_align_by_cell(traces, stim_times, align_to)
            
        except AssertionError:
            warnings.warn('Length of stim times was greater than one but did not match the number of cells. Stim alignment not done.')
    return traces


def make_traces_from_json(path, *args, **kwargs):
    """
    Short cut for loading a json from path and making it into 
    traces=(trials x cell x time). Passes any args and kwargs to process_data.
    """
    data = load_json(path)
    traces = process_data(data['c'], data['splits'], *args, **kwargs)
    return traces

def make_trialwise(traces, splits):
    """Returns trial x cell x time."""
    traces = np.split(traces, np.cumsum(splits[:-1]).astype(np.uint), axis=1)
    shortest = min([s.shape[1] for s in traces])
    return np.array([a[:, :shortest] for a in traces])

def stim_align_by_cell(traces, times, new_start):
    """
    Make stim-aligned PSTHs from trialwise data (eg. trial x cell x time array). The 
    advantage of doing it this way (trialwise) is the trace for each cell gets rolled around
    to the other side of the array, thus eliminating the need for nan padding.

    Args:
        traces (array-like): trial x cell x time array of traces data, typicall from make_trialwise
        times (array-like): list of stim times for each cell, must match exactly, not sure how it
                            handles nans yet...
    """
    psth = np.zeros_like(traces)

    for i in range(traces.shape[0]):
        psth[i,:,:] = np.array([np.roll(cell_trace, -amt+new_start) for cell_trace, amt in zip(traces[i,:,:], times)])

    return psth

def stim_align_all_cells(traces, time, new_start):
    """
    Make stim-aligned PSTHs from trialwise data (eg. trial x cell x time array). The 
    advantage of doing it this way (trialwise) is the trace for each cell gets rolled around
    to the other side of the array, thus eliminating the need for nan padding.

    Args:
        trialwise_traces (array-like): trial x cell x time array of traces data, typicall from make_trialwise
        times (array-like): list of stim times for each cell, must match exactly, not sure how it
                            handles nans yet...
        new_start (int): frame number where the psths will be aligned to
    """
    # FIXME: URGERNT see above, list or single stim time??? depends on how this is working... for a
    # single trial an int is fine, but for multiple trials you'd want to give a list
    psth = np.zeros_like(traces)

    for i in range(traces.shape[0]):
        psth[i,:,:] = np.roll(traces[i,:,:], -int(time[i])+new_start, axis=1)

    return psth

def make_images(caiman_obj):
    Yr, dims, T = cm.load_memmap(caiman_obj.mmap_file)
    return np.reshape(Yr, [T] + list(dims), order='F')

def find_com(A, dims, x_1stPix):
    XYcoords= cm.base.rois.com(A, *dims)
    XYcoords[:,1] = XYcoords[:,1] + x_1stPix #add the dX from the cut FOV
    i = [1, 0]
    return XYcoords[:,i] #swap them

def min_subtract(traces):
    return traces - traces.min(axis=1).reshape(-1,1)

def baseline_subtract(cut_traces, baseline_length):
    baseline = cut_traces[:,:,:baseline_length].mean(axis=2)
    psths_baselined = cut_traces - baseline.reshape(*cut_traces.shape[:2], 1)
    return psths_baselined

def cut_psths(stim_aligned, length=25):
    cut_psths = stim_aligned[:,:,:length]
    return cut_psths

