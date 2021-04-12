function live2pSessionDone(src, evt, varargin)

% global ws
ip = 'localhost';
port = 6000;

ws = Live2pWS(ip, port);
ws.ClientObj.setConnectionLostTimeout(500);

out.EVENTTYPE = 'SESSIONDONE';

ws.send(jsonencode(out))