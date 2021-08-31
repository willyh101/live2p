function live2pVisSocket

    global websocket
    
    % THIS IS WEBSOCKET TO LIVE2P
    visCond = numel(find(diff(ExpStruct.nextsequenceTrigger)>0));
    sendThisCaiman.EVENTTYPE = 'LOG';
    sendThisCaiman.vis_id = visCond;
    
    websocket.send(jsonencode(sendThisCaiman));
    disp('trial data sent to caiman')