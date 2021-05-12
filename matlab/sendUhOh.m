function sendUhOh()

    global ws
    out.EVENTTYPE = 'UHOH';
    
    ws.send(jsonencode(out))