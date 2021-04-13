function live2pSessionDone(src, evt, varargin)

global ws
out.EVENTTYPE = 'SESSIONDONE';

ws.send(jsonencode(out))