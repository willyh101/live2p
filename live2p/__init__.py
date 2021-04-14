from .workers import RealTimeQueue

from importlib_metadata import version

# print('')
# print(f"Welcome to live2p (v{version('live2p')})!")
# print('')
# print('* Note: to quit out you will probably need to close the console window. Ctrl-C is unlikely to work for now...')
# print('* Remember to place your seed image as the only tiff in the current epoch directory!')

msg = f"""
    Welcome to live2p (v{version('live2p')})!

* Note: to quit out you will probably need to close the console window. Ctrl-C is unlikely to work for now...
* Remember to place your seed image as the only tiff in the current epoch directory!
    
Loading...

"""

print(msg)