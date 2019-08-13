#! /usr/bin/env python
import os, string

# load psrchive, set it to not load full data from the files
import psrchive

from math import sin, cos, pi, atan2, asin, trunc

def hms(x):
    ss = x<0
    x = abs(x)
    h = trunc(x)
    m = 60.0*(x-h)
    s = 60.0*(m-trunc(m))
    return'%s%02d:%02d:%05.2f' % ('-' if ss else '+', h, trunc(m), s)

def convert(l,b):
    lr = l*pi/180.0
    br = b*pi/180.0
    (x,y,z) = (cos(lr)*cos(br), sin(lr)*cos(br), sin(br))
    er = 84381.406000/3600.*pi/180.0
    ce = cos(er)
    se = sin(er)
    xq = x
    yq = ce*y - se*z
    zq = se*y + ce*z
    ra = atan2(yq,xq)*12.0/pi
    if ra<0: ra += 24.0
    dec = asin(zq)*180.0/pi
    return (hms(ra) + hms(dec))[1:]

def get_parfile_coords(filename):
    no_amps_bak = psrchive.Profile.no_amps.fget()
    psrchive.Profile.no_amps.fset(True)
    arch = psrchive.Archive_load(filename)
    eph = arch.get_ephemeris()
    psrchive.Profile.no_amps.fset(no_amps_bak)
    ra = eph.get_value('RA')
    if ra=='' or ra==eph.get_value('PMRA'): ra=eph.get_value('RAJ')
    dec = eph.get_value('DECJ')
    if dec=='' or dec==eph.get_value('PMDEC'): dec=eph.get_value('DECJ')
    
    if ra!='' and dec!='':
        return ra+dec

    l = float(eph.get_value('LAMBDA'))
    b = float(eph.get_value('BETA'))
    return convert(l,b)

if __name__=="__main__":
    import sys
    fname = sys.argv[1]
    print get_parfile_coords(fname)
