function live2pAcqDone(src, evt, varargin)

global ws
hSI = src.hSI;

% try to get the saved tiff name at the end of each acquistion
% not sure if this will work
% can send w/o fname and live2p will look for the most recent tiff
out.EVENTTYPE = 'ACQDONE';
out.filename = [hSI.hScan2D.logFilePath '\' hSI.hScan2D.logFileStem '_' sprintf('%05d',hSI.hScan2D.logFileCounter)  '.tif'];
disp(['sent filename: ' out.filename])

ws.send(jsonencode(out))
