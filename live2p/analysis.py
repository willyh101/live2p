"""Backend for handling online analysis of data from caiman."""

import json
import warnings

import numpy as np
import pandas as pd
import scipy.stats as stats
import sklearn

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

def load_json(path):
    with open(path, 'r') as file:
        data_json = json.load(file)
    return data_json

def load_as_obj(caiman_data_path):
    """hdf5 -> caiman object"""
    return cm.source_extraction.cnmf.cnmf.load_CNMF(caiman_data_path)

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

def concat_chunked_data(jsons, f_src='c', *args, **kwargs):
    """
    Takes chunks of data and combines them into a numpy array
    of shape trial x cells x time, concatendated over trials, and
    clips the trials at shortest frame number and fewest cells. Args and
    kwargs are passed to process_data.

    Args:
        jsons (list): list of jsons to process
        f_src (str): key to F data to load ('c' or 'dff'). Defaults to 'c'.

    Returns:
        trial_dat: 3D numpy array, (trials, cells, time)
    """
    # load and format
    c_trials = [load_json(j)[f_src] for j in jsons]
    s_trials = [load_json(j)['splits'] for j in jsons]

    # smoosh all the lists of trials into a big array
    trial_dat = []
    for c,s in zip(c_trials, s_trials):
        out = process_data(c, s, *args, **kwargs)
        trial_dat.append(out)
    
    # ensure that trials are the same length and have same 
    shortest = min([s.shape[2] for s in trial_dat]) # shortest trial
    # fewest = min([c.shape[1] for c in trial_dat]) # fewest cells
    # trial_dat = np.concatenate([a[:, :fewest, :shortest] for a in trial_dat])
    try:
        trial_dat = np.concatenate([a[:, :, :shortest] for a in trial_dat])
    except:
        print('WARNING LOST A CELL(S)!!!!')
        fewest = min([c.shape[1] for c in trial_dat]) # fewest cells
        trial_dat = np.concatenate([a[:, :fewest, :shortest] for a in trial_dat])
    return trial_dat

def posthoc_dff_and_coords(cm_obj):
    cm_obj.estimates.detrend_df_f()
    dff = cm_obj.estimates.F_dff
    
    coords = cm.utils.visualization.get_contours(cm_obj.estimates.A, dims=cm_obj.dims)
    
    return dff, coords

def extract_cell_locs(cm_obj):
    """
    Get the neuron ID, center-of-mass, and coordinates(countors) of all cells from a caiman object. 
    Loads directly from caiman obj or from a string/path and loads the caiman obj.

    Args:
        cm_obj ([caiman, str]): caiman object or path to caiman object

    Returns:
        pd.DataFrame of data
    """
    
    if isinstance(cm_obj, str):
        cm_obj = load_as_obj(cm_obj)
    
    try:
        # this is for normal batch CNMF
        cell_coords = cm.utils.visualization.get_contours(cm_obj.estimates.A, dims=cm_obj.dims)
    except:
        # this is for on acid CNMF
        cell_coords = cm.utils.visualization.get_contours(cm_obj.estimates.A, dims=cm_obj.estimates.dims)
    
    df = pd.DataFrame(cell_coords)
    
     # x and y are flipped here bc rows x cols
    df = pd.concat([df, df.loc[:, 'CoM'].agg(lambda x: x[0]).rename('y')], axis=1)
    df = pd.concat([df, df.loc[:, 'CoM'].agg(lambda x: x[1]).rename('x')], axis=1)
    
    return df

def cut_psths(stim_aligned, length=25):
    cut_psths = stim_aligned[:,:,:length]
    return cut_psths