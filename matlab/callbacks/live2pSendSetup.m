function live2pSendSetup(src, evt, varargin)

% global ws
ip = 'localhost';
port = 6000;

ws = Live2pWS(ip, port);
ws.ClientObj.setConnectionLostTimeout(500);

hSI = src.hSI;

out.EVENTTYPE = 'SETUP';
out.nchannels = length(hSI.hChannels.channelSave);
out.nplanes = hSI.hStackManager.numSlices;
out.fr = hSI.hRoiManager.scanVolumeRate;
out.folder = hSI.hScan2D.logFilePath;


ws.send(jsonencode(out))