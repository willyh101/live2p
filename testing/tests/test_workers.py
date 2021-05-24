import pytest
from pathlib import Path
from caiman.source_extraction.cnmf.online_cnmf import OnACID

def test_no_init(live2p_worker):
    assert live2p_worker.acid is None

def test_initialize_default(live2p_worker):
    live2p_worker.initialize_onacid()
    assert isinstance(live2p_worker.acid, OnACID)
    
@pytest.mark.base_only
def test_folder_structure(base_worker, tiff_path):
    base_path = Path(tiff_path)
    folders = sorted(base_path.glob('live2p*'))
    if len(folders) > 1:
        assert str(len(folders)) in str(base_worker.temp_path.parent)
    else:
        assert str(base_worker.temp_path.parent) == 'live2p'
    
    
    
# def test_initialize_new(live2p_worker):
#     live2p_worker.self.use_prev_init = True
#     acid = live2p_worker.initialize_onacid()
#     assert isinstance(acid, OnACID)

def test_run_queue(live2p_worker):
    pass