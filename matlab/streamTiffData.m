function streamTiffData(frame)

out.data = frame;
out.EVENTTYPE = 'FRAME';
out.plane = 0;
pause(3)
jsonencode(out);

% p = parpool(1);
% 
% r = rand(512,512,100);
% r = int32(r*100);
% 
% for n=1:100
%     tic
%     f(n) = parfeval(@streamTiffData, 0, r(:,:,n));
%     toc
% end