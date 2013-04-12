  function [gtime]=greg2(yd,yr)
% GREG2: converts decimal yearday to standard Gregorian time.
% [gtime]=GREG2(yd,yr) converts decimal yearday to corresponding
% Gregorian calendar dates. In this convention, Julian day 2440000
% begins at 0000 UT May 23 1968.
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
js = julianmd(yr,01,01,00);
%      if you want Julian Days to start at noon...
secs=rem(julian,1)*24*3600;

j = floor(julian) - 1721119;
gtime=[yr(:) mo(:) d(:) hour(:) min(:) sec(:)];