def test_tf():
    import tensorflow as tf
    
    print(f'Tensorflow version: {tf.__version__}')
    
    if tf.test.is_built_with_cuda():
        print('Tensorflow built with CUDA')
    else:
        print('*** FAILED: Tensorflow NOT built with CUDA ***')
    
    if tf.test.is_gpu_available():
        print('Tensorflow successfully found the GPU')
    else:
        print('*** FAILED: GPU not found by tensorflow ***')
        
def test_cuda():
    try:
        import pycuda.gpuarray as gpuarray
        import pycuda.driver as cudadrv
        import atexit
        HAS_CUDA = True
    except ImportError:
        HAS_CUDA = False
        
    if HAS_CUDA:
        print('pycuda loaded successfullly')
    else:
        print('*** FAILED: pycuda ImportError ***')
        
def main():
    test_tf()
    test_cuda()
    
if __name__ == '__main__':
    main()