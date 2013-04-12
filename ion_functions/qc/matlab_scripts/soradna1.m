function [z,sorad]=soradna1(yd,yr,long,lat)
% SORADNA1: computes no-sky solar radiation and solar altitude.
% [z,sorad]=SORADNA1(yd,yr,long,lat) computes instantaneous values of
% solar radiation and solar altitude from yearday, year, and position
% data. It is put together from expressions taken from Appendix E in the
% 1978 edition of Almanac for Computers, Nautical Almanac Office, U.S.
% Naval Observatory. They are reduced accuracy expressions valid for the
% years 1800-2100. Solar declination computed from these expressions is
% accurate to at least 1'. The solar constant (1368.0 W/m^2) represents a
% mean of satellite measurements made over the last sunspot cycle (1979-1995)
% taken from Coffey et al (1995), Earth System Monitor, 6, 6-10. Assumes
% yd is either a column or row vector, the other input variables are scalars,
% OR yd is a scalar, the other inputs matrices.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 3/8/97: version 1.0
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% convert yd to column vector if necessary
% convert to new variables
% two options - either long/lat are vectors, time is a scalar
if length(SC)==1,
% constants
% compute Universal Time in hours
% compute Julian ephemeris date in days (Day 1 is 1 Jan 4713 B.C.=-4712 Jan 1)
% compute interval in Julian centuries since 1900
% compute mean anomaly of the sun
% compute mean longitude of sun
% compute mean anomaly of Jupiter

% compute longitude of the ascending node of the moon's orbit
% compute mean anomaly of Venus
% compute sun theta
% compute sun rho
% compute declination
% compute equation of time (in seconds of time) (L in degrees)
% compute local hour angle
% compute radius vector
% compute solar radiation outside atmosphere