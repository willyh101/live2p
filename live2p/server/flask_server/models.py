import json
import queue

import numpy as np
import scipy.io as sio

from ...analysis import process_data

class Experiment:
    def __init__(self):
        self.output_folder = None
        self.params = None
        self.Ain_path = None
        self.num_frames_max = 10000
        self.init_files = None
        self.lengths = []
        self.nchannels = None
        self.nplanes = None
        self.fr = None
        self.xslice = slice(0,512)
        self.yslice = slice(0,512)
        self.use_prev_init = False
        self.si_path = None
        self.qs = []
            
    def update(self, data):
        """Update the Experiment object with an incoming dict/json."""
        for key, value in data.items():
            setattr(self, key, value)
            
    def process_and_save(self, results):
        c_list = [r['C'] for r in results]
        c_all = np.concatenate(c_list, axis=0)
        out = {
            'c': c_all.tolist(),
            'splits': self.lengths
        }
        
        # first save the raw data in case it fails (concatentated)
        fname = self.output_folder/'raw_data.json'
        with open(fname, 'w') as f:
            json.dump(out, f)
        
        # do proccessing and save trialwise json
        traces = process_data(**out, normalizer='scale')
        out = {
            'traces': traces.tolist()
        }
        fname = self.output_folder/'traces_data.json'
        with open(fname, 'w') as f:
            json.dump(out, f)
            
        # save it as a npy also
        fname = self.output_folder/'traces.npy'
        np.save(fname, c_all)
        fname = self.output_folder/'psths.npy'
        np.save(fname, traces)
        
        # save as matlab
        fname = self.output_folder/'data.mat'
        mat = {
            'tracesCaiman': c_all,
            'psthsCaiman': traces,
            'trialLengths': self.lengths
        }
        sio.savemat(fname, mat)
        
    def make_queues(self):
        self.qs = [queue.Queue for q in range(self.nplanes)]