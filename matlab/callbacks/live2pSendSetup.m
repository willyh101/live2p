function live2pSendSetup(src, evt, varargin)

global ws
hSI = src.hSI;

out.EVENTTYPE = 'SETUP';
out.nchannels = length(hSI.hChannels.channelSave);
out.nplanes = hSI.hStackManager.numSlices;
out.fr = hSI.hRoiManager.scanVolumeRate;
out.folder = hSI.hScan2D.logFilePath;
% need to grab these from workspace somehow
% out.xmin = min(Opts.width);
% out.xmax = max(Opts.width);
% out.sources = sources;


ws.send(jsonencode(out))

% send message to start up the queues
clear out
out.EVENTTYPE = 'START';
ws.send(jsonencode(out))