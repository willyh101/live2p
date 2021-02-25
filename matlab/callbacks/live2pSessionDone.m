function live2pSessionDone(src, evt, varargin)

global ws

out.event = 'SESSIONDONE';

ws.send(jsonencode(out))