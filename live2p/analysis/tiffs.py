import pickle
from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.offsetbox import AnchoredText
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
from ScanImageTiffReader import ScanImageTiffReader
from skimage import exposure
from tqdm import tqdm

from ..guis import openfilegui

class SItiff:
    def __init__(self, path) -> None:
        self.path = str(path)
        
        self._metadata = metadata_to_dict(self.path)
        
        chans = self._eval_numeric_metadata('channelSave')
        if isinstance(chans, int):
            self.nchannels = 1
        else:
            self.nchannels = len(chans)
            
        self.fr = self._eval_numeric_metadata('scanVolumeRate')
        self.zs = self._eval_numeric_metadata('zs')
        self.nplanes = len(self.zs)
        
        with ScanImageTiffReader(self.path) as reader:
            self.data = reader.data()
    
    def _eval_numeric_metadata(self, key):
        return eval(self._metadata[key].replace(' ',',').replace(';',','))
        
    def mean_img(self, z_idx, channel, scaling=None, as_rgb=False, rgb_ch=None, blue_as_cyan=True):
        tslice = get_tslice(z_idx, channel, self.nchannels, self.nplanes)
        mimg = np.mean(self.data[tslice,:,:], axis=0)
        mimg -= mimg.min()
        
        if scaling:
            mimg = exposure.rescale_intensity(mimg, scaling)
            
        if as_rgb:
            rgb_im = np.zeros((*mimg.shape,3))
            if not rgb_ch:
                if channel == 1:
                    rgb_ch = 0
                elif channel == 0:
                    rgb_ch = 1
                else: 
                    rgb_ch = channel
            rgb_im[:,:,rgb_ch] = mimg
            
            if blue_as_cyan and rgb_ch == 2:
                rgb_im[:,:,1] = mimg
            
            return rgb_im
        
        else:   
            return mimg
    
    def merge_mean(self, z_idx, gscale=None, rscale=None, green_as_cyan=False):
        green_ch = self.mean_img(z_idx, 0, scaling=gscale)
        red_ch = self.mean_img(z_idx, 1, scaling=rscale)
        
        rgb_im = np.zeros((*green_ch.shape, 3))
        rgb_im[:,:,0] = red_ch
        rgb_im[:,:,1] = green_ch
        
        if green_as_cyan:
            rgb_im[:,:,2] = green_ch
            
        return rgb_im
    
    def show(self, z_idx, ch_idx, scaling=None, as_rgb=False, rgb_ch=None, ax=None, 
             ch_label_txt=None, ch_label_color='white', **kwargs):
        
        if ax is None:
            ax = plt.gca()
            
        mean_img = self.mean_img(z_idx, ch_idx, scaling=scaling, as_rgb=as_rgb, rgb_ch=rgb_ch, **kwargs)
        
        
        # note I don't think this will work will multiple colors since you can't specify
        fontdict = {
            'size':18,
            'color':ch_label_color
        }
        label = AnchoredText(ch_label_txt, loc='upper left', prop=fontdict,
                             frameon=False, pad=0.2, borderpad=0.2)
        
        fontprops = fm.FontProperties(size=18)
        scalebar = AnchoredSizeBar(ax.transData, 
                                128,
                                f'200 $\mu$m',
                                'lower right',
                                pad=0.2,
                                color='white',
                                frameon=False,
                                size_vertical=8,
                                fontproperties=fontprops)
        ax.add_artist(scalebar)
        ax.add_artist(label)
        ax.imshow(mean_img)
        ax.axis('off')
        
        return ax
    
    @classmethod
    def load(cls, rootdir='d:/frankenrig/experiments'):
        path = openfilegui(rootdir=rootdir, title='Select Tiff')
        if not path:
            return
        print(f'Loading tiff: {path}')
        return cls(path)
    
    
    
    
def metadata_to_dict(file):
    """Read the SI metadata and turn in into a dict. Does not cast/eval values."""
    
    with ScanImageTiffReader(file) as reader:
        meta = reader.metadata()
    
    # split at the new line marker
    meta = meta.split('\n')
    # filter out the ROI data by keeping fields that start with SI.
    meta = list(filter(lambda x: 'SI.' in x, meta))
    # make dictionary by splitting at equals, and only keep the last part of the fieldname as the key
    d = {k.split('.')[-1]:v for k,v in (entry.split(' = ') for entry in meta)}
    
    return d

def get_tslice(z_idx, ch_idx, nchannels, nplanes):
    return slice((z_idx*nchannels)+ch_idx, -1, nplanes*nchannels)

def slice_movie(mov_path, x_slice, y_slice, t_slice):
    """
    Slice a single tiff along x, y, and time dims. Time dim must account for number of channels and
    z-planes. slice((z_idx*nchannels)+channel, -1, nplanes*nchannels)

    Args:
        mov_path (str): path to movie
        x_slice (slice): slice along x-axis
        y_slice (slice): slice along y-axis
        t_slice (slice): slice along t-axis

    Returns:
        np.array: array of sliced movie
    """
    with ScanImageTiffReader(mov_path) as reader:
        data = reader.data()
        data = data[t_slice, y_slice, x_slice]
    return data

def count_tiff_lengths(movie_list, save=False):
    """
    Counts the length of tiffs for a single plane and channel to get trial lenths. Optionally save
    the data to dist as a pickle.

    Args:
        movie_list (list): list of str or Path pointing to the tiffs to count.
        save (bool or str, optional): Whether to save the file. can either set to True to save in
                                      in the folder with the counted tiffs or specify save location
                                      with a string. Defaults to False.

    Returns:
        numpy array of tiff/trial lengths
    """
    movie_list = list(movie_list)
    first_tiff = SItiff(movie_list[0])
    t_slice = get_tslice(0, 0, first_tiff.nchannels, first_tiff.nplanes)
    nframes = [slice_movie(str(mov), slice(None), slice(None), t_slice).shape[0] for mov in tqdm(movie_list, desc="Counting Tiffs: ")]
    
    if save:
        if isinstance(save, str):
            save_path = Path(save, 'tiff_lengths.pickle')
        else:
            save_path = Path(first_tiff.path).parent/'tiff_lengths.pickle'
            
        with open(save_path, 'wb') as f:
            pickle.dump(nframes, f)
    
    return np.array(nframes)

def tiffs2array(movie_list, x_slice, y_slice, t_slice):
    data = [slice_movie(str(mov), x_slice, y_slice, t_slice) for mov in movie_list]
    return np.concatenate(data)
