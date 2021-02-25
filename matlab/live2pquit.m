% remove callbacks
sendsetup = arrayfun(@(x) strcmp(x.UserFcnName,'live2pSendSetup'), hSI.hUserFunctions.userFunctionsCfg);
if any(sendsetup)
    hSI.hUserFunctions.userFunctionsCfg(sendsetup) = [];
end

acqdone = arrayfun(@(x) strcmp(x.UserFcnName,'live2pAcqDone'), hSI.hUserFunctions.userFunctionsCfg);
if any(acqdone)
    hSI.hUserFunctions.userFunctionsCfg(acqdone) = [];
end

acqsessionend = arrayfun(@(x) strcmp(x.UserFcnName,'live2pSessionDone'), hSI.hUserFunctions.userFunctionsCfg);
if any(acqdone)
    hSI.hUserFunctions.userFunctionsCfg(acqsessionend) = [];
end

% remove paths
rmpath(genpath('C:\Users\FrankenSI\Documents\live2p\matlab'))
rmpath(genpath('C:\Users\FrankenSI\Documents\MATLAB\MatlabWebSocket\src'))