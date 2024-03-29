import warnings

import numpy as np
import pandas as pd
import scipy.stats as stats
import sklearn.preprocessing

def process_data(raw_traces, trial_lengths, fr, new_start=1, norm_method='scale', stim_times=None, total_length=None, **kwargs):
    """
    Run the post-processing pipeline on traces. Performs min subtraction, normalizes the data, and
    makes it into trialwise data (trials, cells, time). Optionally run stim alignment (either by 
    stim times per cell or stim times per trial). Performs a trialwise baseline subtraction. Finally, 
    optionally cut the PSTHs to a specified length.
    
    Normalization methods:
        * 'none' for no normalization or
        * from sklearn.preprocessing:
            - 'scale' = mean subtracted - std
            - 'minmax' = scaled to min max (not abs)
            - 'norm' = L2 norm
        * from scipy.stats:
            - 'zscore' = traditional zscoring
        

    Args:
        raw_traces (array-like): Raw data, typically either C or nC
        trial_lengths (array-like): lengths of each trial in frames
        fr (float or int): frame rate of acquisition, per plane
        new_start (float or int): time in seconds to align data to
        norm_method (str, optional): Normalization method. Defaults to 'scale' (see above).
        stim_times (array-like, optional): List of stim times that is lengths of trials or cells. Defaults to None.
        total_length (float or int, optional): Desired length of PSTHs. Defaults to None (no cutting).

    Returns:
        traces (cells, frames)
        trailwise_data (trials, cells, frames)
    """
    
    # min subtract and normalize
    data  =  np.array(raw_traces)
    data = min_subtract(data)
    
    traces = normalize_data(data, norm_method)
    
    # make data trialwise
    trialwise_data = make_trialwise(traces, trial_lengths) # trials, cells, time
    
    # stimtime alignment (either by cell or by trial)
    new_start *= fr
    new_start = int(new_start)
    if stim_times is not None:
        stim_times = np.array(stim_times)
        stim_times *= fr
        trialwise_data = stimalign(trialwise_data, stim_times, new_start)
    
    # baseline subtract data for each trial
    baseline_length = new_start - 1
    trialwise_data = baseline_subtract(trialwise_data, baseline_length)
    
    # optionally cut psths to length
    if total_length is not None:
        total_length *= fr
        total_length = int(total_length)
        trialwise_data = cut_psths(trialwise_data, length=total_length)
    
    return traces, trialwise_data

def stimalign(trialwise_data: np.ndarray, stim_times: np.ndarray, new_start: int):
    stim_times = stim_times.round().astype(int)
    stim_times[np.isnan(stim_times)] = 0 # this is one way to handle cells that don't get stimmed
    
    aligned_data = np.zeros_like(trialwise_data)
    if len(stim_times) == trialwise_data.shape[1]: # aka number of cells, like stim test
        for i in range(trialwise_data.shape[0]):
            aligned_data[i,...] = np.array([np.roll(cell_trace, -amt+new_start) for cell_trace, amt in zip(trialwise_data[i,...], stim_times)])
    
    elif len(stim_times) == trialwise_data.shape[0]: # aka number of trials, like ori epoch, although note this breaks in true online mode bc last tiff
        for i in range(trialwise_data.shape[0]):
            aligned_data[i,...] = np.roll(trialwise_data[i,...], -int(stim_times[i])+new_start, axis=1)
            
    # TODO: eventually add support for trial x cell stim times (unique each trial)
    else:
        warnings.warn('Length of stim times did not match the number of cells or number of trials. Stim alignment not done.')
            
    return aligned_data

def make_trialwise(traces, splits):
    """Returns trial x cell x time."""
    traces = np.split(traces, np.cumsum(splits[:-1]).astype(np.uint), axis=1)
    shortest = min([s.shape[1] for s in traces])
    return np.array([a[:, :shortest] for a in traces])

def min_subtract(traces):
    return traces - traces.min(axis=1).reshape(-1,1)

def baseline_subtract(cut_traces, baseline_length):
    baseline = cut_traces[:,:,:baseline_length].mean(axis=2)
    psths_baselined = cut_traces - baseline.reshape(*cut_traces.shape[:2], 1)
    return psths_baselined

def cut_psths(stim_aligned, length=25):
    cut_psths = stim_aligned[:,:,:length]
    return cut_psths

def rolling_baseline_dff(traces):
    f0s = pd.DataFrame(traces.T).rolling(200, min_periods=1, center=True).quantile(0.2)
    f0s = f0s.values.T
    traces = (traces-f0s)/f0s
    return traces

def normalize_data(data, norm_method):
    normalize_func = {
        'none': data, # nothing done...
        'minmax': lambda x: sklearn.preprocessing.minmax_scale(x, axis=1), # scaled to min max (not abs)
        'zscore': lambda x: stats.zscore(x, axis=1), # old fashion zscoring
        'norm': lambda x: sklearn.preprocessing.normalize(x, axis=1), # L2 norm
        'scale': lambda x: sklearn.preprocessing.scale(x, axis=1), # mean subtracted, divided by standard dev
    }.get(norm_method)
        
    return normalize_func(data)
