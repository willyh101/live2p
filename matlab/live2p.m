% copy this file to somewhere on your matlab path

%%-----PATHING-----%%
% make sure that live2p/matlab is on path and matlabwebsocket
% these will be specific to your installation
addpath(genpath('C:\Users\FrankenSI\Documents\live2p\matlab'))
addpath(genpath('C:\Users\FrankenSI\Documents\MATLAB\MatlabWebSocket\src'))


%%-----WEBSOCKET-----%%
% set ip and port of the server here
ip = 'localhost';
port = 6000;

% start websocket
global ws
ws = Live2pWS(ip, port);


% activate user functions
% first remove any existing caiman fxns then activate them
sendsetup = arrayfun(@(x) strcmp(x.UserFcnName,'sendSetup'), hSI.hUserFunctions.userFunctionsCfg);
if any(sendsetup)
    hSI.hUserFunctions.userFunctionsCfg(sendsetup) = [];
end

acqdone = arrayfun(@(x) strcmp(x.UserFcnName,'live2pAcqDone'), hSI.hUserFunctions.userFunctionsCfg);
if any(acqdone)
    hSI.hUserFunctions.userFunctionsCfg(acqdone) = [];
end

acqsessionend = arrayfun(@(x) strcmp(x.UserFcnName,'live2pSessionDone'), hSI.hUserFunctions.userFunctionsCfg);
if any(acqsessionend)
    hSI.hUserFunctions.userFunctionsCfg(acqsessionend) = [];
end

fxn.EventName = 'acqModeArmed';
fxn.UserFcnName = 'live2pSendSetup';
fxn.Arguments = {};
fxn.Enable = 1;
hSI.hUserFunctions.userFunctionsCfg(end+1) = fxn;

fxn.EventName = 'acqDone';
fxn.UserFcnName = 'live2pAcqDone';
fxn.Arguments = {};
fxn.Enable = 1;
hSI.hUserFunctions.userFunctionsCfg(end+1) = fxn;

fxn.EventName = 'acqAbort';
fxn.UserFcnName = 'live2pSessionDone';
fxn.Arguments = {};
fxn.Enable = 1;
hSI.hUserFunctions.userFunctionsCfg(end+1) = fxn;