function live2pStimSocket

global ExpStruct
global live2p_ws

seqNum = numel(find(diff(ExpStruct.triggerPuffer)==1));

if seqNum > numel(ExpStruct.bigListofSequences)
    sendThis = [1000];
    sendThisSI = [];
elseif seqNum ==0
    disp('0 trials')
    sendThis = [];
    sendThisSI.times  = ExpStruct.bigListOfFirstStimTimes(:,1);
    sendThisSI.power  = 0;
    sendThisSI.spikes = 0;
    sendThisSI.rates     = 0;
else
    sendThis          = ExpStruct.bigListofSequences{seqNum};
    sendThisSI.times  = ExpStruct.bigListOfFirstStimTimes(:,seqNum);
    sendThisSI.power  = ExpStruct.powerList(seqNum);
    sendThisSI.spikes = ExpStruct.pulseList(seqNum);
    sendThisSI.rates  = ExpStruct.hzList(seqNum); 
end

% THIS IS MSOCKET TO HOLO
%make sure you've received the handshake before sending
if ~isempty(sendThis)
    invar=[]; t= tic;
    while ~strcmp(invar,'C') && toc(t)<0.1;
        invar = msrecv(ExpStruct.Socket,.5);
    end
    if toc(t)>0.1
        disp('SLM handshake error')
    else
        disp('recieved handshake from SLM ');
    end
    mssend(ExpStruct.Socket, sendThis) ;
    disp('Sent SLM')
end

% THIS IS MSOCKET TO SI
invar=[]; t=tic;
while (~strcmp(invar,'start') && ~strcmp(invar,'received') ) && toc(t)<0.2
    invar = msrecv(ExpStruct.SISocket,.5);
end
toc(t)
if toc(t)>0.2
    disp('SI handshake error')
else
    disp(['recieved handshake from SI, it says ' invar]);
end
flushMSocket(ExpStruct.SISocket);
disp('sending to SI');
mssend(ExpStruct.SISocket, sendThisSI);

% THIS IS WEBSOCKET TO LIVE2P

visCond = numel(find(diff(ExpStruct.nextsequenceTrigger)>0));
sendThisCaiman.EVENTTYPE = 'LOG';
sendThisCaiman.stim_cond = sendThisSI.power;
sendThisCaiman.stim_times = sendThisSI.times;
sendThisCaiman.vis_id = visCond;

live2p_ws.send(jsonencode(sendThisCaiman));
disp('trial data sent to caiman')