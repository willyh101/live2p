# Live2p

**Live2p** - online implentation of [CaImAn](https://github.com/flatironinstitute/CaImAn) for realtime analysis 2-photon calcium imaging with [ScanImage](http://scanimage.vidriotechnologies.com/).

## Installation

1. Download and install [miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda 3](https://www.anaconda.com/products/individual) if you haven't already. Click YES to add conda to PATH. It's not actually required just useful in general.

1. Clone this repo using command-line git or GitHub desktop as I will be updating/bug-fixing.

1. Open anaconda/miniconda prompt and change to the directory where you put live2p (`cd path/to/live2p/folder`)

1. Install live2p with:  `conda env create -f environment.yml`. This will install live2p, python, and all other packages you need to set up and run the websocket servers, do analysis, etc.

1. Activate the environment `conda activate live2p`

1. Install the live2p package by running `pip install -e .` (the . is intentional) On some machines you may need to run `pip3 install -e .` if the previous fails.

1. Lastly, download and install the most recent [MatlabWebsocket](https://github.com/jebej/MatlabWebSocket) from GitHub. Follow their install instructions.

## Setup

Getting setup to run is involves 1) making and running a `rig_run.py`  file, 2) getting ScanImage callbacks enabled and websocket ready in MATLAB, and 3) starting an actual experiment.

### Rig_run file

This file will run the server that ScanImage will talk to (currently via websockets). It's pretty simple but holds a lot of important settings, some of which I will go through here. See the `example_run.py` file in the rig_files folder for more details. **Please create your own file for your rig.**

* The OnACID algorithm is very sensitive to time varying changes in fluorescence so we have to exclude any and all artifacts from visual or holograhic stimulation. Set `x_start` and `x_end` accordingly. If you are seeding the algorithm with spatial components (eg. sources from makeMasks3D) **it is extremely important that `x_start` and `x_end` match what you used in makeMasks3D**.

* Set the mode you are running. This can be either `'seeded'` or `'unseeded'`. This will use default settings from the corresponding dictionary to setup CaImAn.

* Set the IP and port to run on. Defaults are usually fine.

* Set the output folder to where the final data gets saved. Could be a folder on your data drive or on a server somewhere. It doesn't really matter. (_note: the data saved there will be overwritten with each run of live2p_) The output data is also saved into the same folder where your tiffs are and that does NOT need to be specified.

* `template_path` needs to be set to a place where you save MM3D. I just added a line in makeMasks3D to save the .mat file to save to this location everytime.

## Running an experiment

### Start live2p server

- First, you need to start the live2p server. You can do this by:

- A) from VSCode, directly running your rig_run.py file to start the live2p server with the green 'play' button at the top right of the screen or 

- B) by opening an Anaconda/conda enabled commandline, activating the environment `conda activate live2p` and then simply entering `live2p`.

### Enable MATLAB callbacks and connect
To interface with the server you will need to enable some MATLAB callbacks. There is a single function that enables and activates them for convenience.

1. Copy the file `matlab/live2p` to somewhere on your MATLAB path. Then, under PATHING and WEBSOCKET headings, change the paths so they are correct for your PC and the IP and port to whatever you want to use. **Port and IP must match whatever is in the rig_run.py file or nothing works.**

1. Collect 500 frames of data. If you can add visual stimulation the algorithm might work better, but you don't have to.

1. Run the command `live2p` in MATLAB. This enables everything and setups up the websocket client. Do this *after* you collect your seed data because this command will enable some callback functions.

1. Create a new folder that this epoch's tiffs will go into and change SI to save to that folder.

1. Get everything ready and hit `LOOP`. Live2p uses CaImAn OnACID which needs to be seeded with some initial data. Live2p will run initialization for each plane, which should take about 30 seconds for each plane. *If there are no tiffs in the epoch folder you will be prompted to select file(s) to seed from*.

1. Once live2p is finished initializing, you can start running your experiment!

1. Once you are done, run the command `quit2p` in the MATLAB commandline. This disconnects from the live2p server and disables the callback functions.

1. If you are going to do another epoch with live2p, restart live2p from VSCode/anaconda prompt and then run `live2p` in MATLAB again.