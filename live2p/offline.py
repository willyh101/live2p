import logging
import time
from pathlib import Path
from multiprocessing import Process, Queue
import json

from ScanImageTiffReader import ScanImageTiffReader

from .utils import get_nchannels, get_nvols, get_tslice, slice_movie
from .workers import RealTimeQueue

logger = logging.getLogger('live2p')

def append_to_queue(q, tiff_folder, tslice, add_rate=1):
    
    tiff_list = Path(tiff_folder).glob('*.tif*')
    lengths = []
    
    for i,t in enumerate(tiff_list):
        # open data
        logger.debug(f'Adding tiff {i}.')
        with ScanImageTiffReader(str(t)) as reader:
           data = reader.data()
           
        # check if valid tiff
        if data.shape[0] > 15:    
            # slice movie for this plane
            mov = data[tslice, :, :]
            lengths.append(mov.shape[0])
            
            # add frames to the queue
            for f in mov:
                q.put(f.squeeze())         
        else:
            continue   
        # so we don't overload memory
        time.sleep(add_rate)  
            
    fname = Path(tiff_folder,'file_lengths.json')
    data = dict(lengths=lengths)
    with open(fname, 'w') as f:
        json.dump(data, f)
        
    q.put('STOP')
    
    
def run_plane_offline(plane, tiff_folder, params, x_start, x_end, 
                      n_init=500, max_frames=30000, add_rate=1, **kwargs):
    
    q = Queue()
    xslice = slice(x_start, x_end)
    tiff_files = Path(tiff_folder).glob('*.tif*')
    mm3d_file = str(list(Path(tiff_folder).glob('*makeMasks3D_img.mat'))[0])
    
    if not mm3d_file:
        logger.error(f'No makeMasks3D found at: {mm3d_file}')
        raise FileNotFoundError
    
    init_list, nchannels, nplanes, tslice = prepare_init(plane, n_init, tiff_files)    
    
    # once you have gotten the tiffs for init, run the queue
    print('starting initialization...')
    worker = RealTimeQueue(init_list, plane, nchannels, nplanes, params, q,
                           num_frames_max=max_frames, Ain_path=mm3d_file,
                           xslice=xslice, **kwargs)
        
    print('starting queue...')
    queue_p = Process(target=append_to_queue, args=(q, tiff_folder, tslice, add_rate))
    # queue_p = Thread(target=append_to_queue, args=(q, tiff_folder, tslice, add_rate))
    queue_p.start()
    
    print('starting worker...')
    result = worker.process_frame_from_queue()
    queue_p.join()
    queue_p.close()
    print('done!')
    
    return result

def prepare_init(plane: int, n_init: int, tiff_files: list):
    nframes = 0
    init_list = []
    print('getting files for initialization....')
    while nframes < n_init:
        tiff = next(tiff_files)
        if nframes == 0:
            nchannels = get_nchannels(str(tiff))
            nplanes = get_nvols(str(tiff))
            tslice = get_tslice(plane, 0, nchannels, nplanes)
        length = slice_movie(str(tiff), slice(None), slice(None), tslice).shape[0]
        init_list.append(tiff)
        nframes += length
    return init_list,nchannels,nplanes,tslice

def run_plane_offline_multifolder(plane, tiff_folders, params, x_start, x_end,
                                  n_init=500, max_frames=30000, add_rate=0.5, **kwargs):
    q = Queue()
    xslice = slice(x_start, x_end)
    
    tiff_files_init = Path(tiff_folders[0]).parent.rglob('*.tif*')
    mm3d_file = str(list(Path(tiff_folders[0]).parent.glob('*makeMasks3D_img.mat'))[0])
    
    if not mm3d_file:
        logger.error(f'No makeMasks3D found at: {mm3d_file}')
        raise FileNotFoundError
    
    # fix this  to take multi folders!!!
    init_list, nchannels, nplanes, tslice = prepare_init(plane, n_init, tiff_files_init) 
    
    # once you have gotten the tiffs for init, run the queue
    print('starting initialization...')
    worker = RealTimeQueue(init_list, plane, nchannels, nplanes, params, q,
                           num_frames_max=max_frames, Ain_path=mm3d_file,
                           xslice=xslice, **kwargs)
    
    print('starting queue...')
    queue_p = Process(target=append_to_queue_multifolder, args=(q, tiff_folders, tslice, add_rate))
    # queue_p = Thread(target=append_to_queue, args=(q, tiff_folder, tslice, add_rate))
    queue_p.start()
    
    print('starting worker...')
    result = worker.process_frame_from_queue()
    queue_p.join()
    queue_p.close()
    print('done!')
    
    # return result

def append_to_queue_multifolder(q, tiff_folders, tslice, add_rate=1):
    # first, iterate through the epochs
    files_per_epoch = []
    lengths_list = []
    for tiff_folder in tiff_folders:
        tiff_list = Path(tiff_folder).glob('*.tif*')
        f_count =  0
        lengths = []
        # then through files in each epoch
        for i,t in enumerate(tiff_list):
            # open data
            logger.debug(f'Adding tiff {i}.')
            with ScanImageTiffReader(str(t)) as reader:
                data = reader.data()
                
            # check if valid tiff
            if data.shape[0] > 15:    
                # slice movie for this plane
                mov = data[tslice, :, :]
                lengths.append(mov.shape[0])
                f_count += 1
                # add frames to the queue
                for f in mov:
                    q.put(f.squeeze())         
            else:
                continue   
            # so we don't overload memory
            time.sleep(add_rate)
        
        # append the file count per epoch
        files_per_epoch.append(f_count)
        lengths_list.append(lengths)
                
    fname = Path(tiff_folders[0],'file_lengths.json')
    data = dict(lengths=lengths_list, files_per_epoch=files_per_epoch)
    with open(fname, 'w') as f:
        json.dump(data, f)
        
    q.put('STOP')