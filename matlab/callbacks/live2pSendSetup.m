function live2pSendSetup(src, evt, varargin)

global ws
hSI = src.hSI;

out.EVENTTYPE = 'SETUP';
out.nchannels = length(hSI.hChannels.channelSave);
out.nplanes = hSI.hStackManager.numSlices;
out.fr = hSI.hRoiManager.scanVolumeRate;
out.folder = hSI.hScan2D.logFilePath;

ws.send(jsonencode(out))