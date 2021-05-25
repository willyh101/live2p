import pytest

@pytest.fixture
def tf():
    import tensorflow as tf
    return tf

def test_tf_version(tf):
    major_version = int(tf.__version__.split('.')[0])
    assert major_version >= 2
    
def test_tf_cuda(tf):
    assert tf.test.is_built_with_cuda()
    
def test_tf_gpu(tf):
    assert tf.test.is_gpu_available()
        
def test_cuda():
    try:
        import pycuda.gpuarray as gpuarray
        import pycuda.driver as cudadrv
        import atexit
        has_cuda = True
    except ImportError:
        has_cuda = False
        
    assert has_cuda