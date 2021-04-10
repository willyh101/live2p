function live2pAcqDone(src, evt, varargin)

% global ws
ip = 'localhost';
port = 6000;

ws = Live2pWS(ip, port);
ws.ClientObj.setConnectionLostTimeout(500);
hSI = src.hSI;

% try to get the saved tiff name at the end of each acquistion
% not sure if this will work
% can send w/o fname and live2p will look for the most recent tiff
out.EVENTTYPE = 'ACQDONE';
out.filename = [hSI.hScan2D.logFilePath '_' sprintf('%05d',hSI.hScan2D.logFileCounter)];
disp(['sent filename: ' out.filename])

ws.send(jsonencode(out))
