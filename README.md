# Live2p

**Live2p** - online implentation of [CaImAn](https://github.com/flatironinstitute/CaImAn) for realtime analysis 2-photon calcium imaging with [ScanImage](http://scanimage.vidriotechnologies.com/).

## Installation

1. Download and install [miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda 3](https://www.anaconda.com/products/individual) if you haven't already. Click YES to add conda to PATH. It's not actually required just useful in general.

1. Clone this repo using command-line git or GitHub desktop as I will be updating/bug-fixing.

1. Open anaconda/miniconda prompt and change to the directory where you put live2p (`cd path/to/live2p/folder`)

1. Install live2p with:  `conda env create -f environment.yml`. This will install live2p, python, and all other packages you need to set up and run the websocket servers, do analysis, etc.

1. Activate the environment `conda activate live2p`

1. Install the caiman_online package by running `pip install -e .` (the . is intentional)

1. Lastly, download and install the most recent [MatlabWebsocket](https://github.com/jebej/MatlabWebSocket) from GitHub. Follow their install instructions.

## Setup

Getting setup to run is involves 1) making and running a `rig_run.py`  file, 2) getting ScanImage callbacks enabled and websocket ready in MATLAB, and 3) starting an actual experiment.

### Rig_run file

This file will run the server that ScanImage will talk to (currently via websockets). It's pretty simple but holds a lot of important settings, some of which I will go through here. See the `example_run.py` file in the rig_files folder for more details. Create your own file for your rig.

* The OnACID algorithm is very sensitive to time varying changes in fluorescence so we have to exclude any artifacts from visual or holograhic stimulation. Set `x_start` and `x_end` accordingly (`y_start` and `y_end` are available also, but less important). If you are seeding the algorithm with spatial components (eg. sources from makeMasks3D) **it is extremely important that `x_start` and `x_end` match what you used in makeMasks3D**.

* Set `max_frames` to something that definitely exceeds the total number of frames you might collect (on a per-plane basis). This is an upper limit.

* Set the mode you are running. This can be either `'seeded'` or `'unseeded'`. This will use default settings from the corresponding dictionary to setup CaImAn.

* Set the IP and port to run on. Defaults are usually fine.

* Set the output folder to where the final data gets saved. Could be a folder on your data drive or on a server somewhere. It doesn't really matter. (_note: the data saved there will be overwritten with each run of live2p_) The output data is also saved into the same folder where your tiffs are and that does not need to be specified.

To be continued...