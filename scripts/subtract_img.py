#! /usr/bin/env python

import numpy
from numpy.fft import rfft, irfft
import psr_utils
import psrchive

def smear_profile(prof,fac):
    nb = len(prof)
    bmax = int(1.0/fac/2.0)
    if bmax>nb/2: bmax=nb/2
    fprof = rfft(prof)
    fprof[bmax:] = 0.0
    return irfft(fprof)

fname = 'guppi_55670_J1744-1134_0010.8y'
arch = psrchive.Archive_load(fname + '.T')
arch.remove_baseline()
sub = arch[0]
nchan = arch.get_nchan()
nbin = arch.get_nbin()
dm = arch.get_dispersion_measure()
chbw = sub.get_bandwidth()/nchan

dat = arch.get_data()
dat_f = 0.0*dat
dat_s = 0.0*dat

r = 0.00970*2.

for i in range(1,nchan/2):
#for i in range(1,nchan):

    f0 = sub.get_centre_frequency(i)
    f1 = sub.get_centre_frequency(nchan-i)

    p = sub.get_folding_period()

    smear = (psr_utils.dm_smear(dm,chbw,f0) 
            + psr_utils.dm_smear(dm,chbw,f1)) / p

    delay = (psr_utils.delay_from_DM(dm,f0) 
            - psr_utils.delay_from_DM(dm,f1)) / p

    delay -= int(delay)
    if delay<-0.5: delay += 1.0
    if delay>0.5: delay -= 1.0

    #print i, smear, delay


    for pol in range(2):

        if fabs(delay)>0.1:
            dat_f[0,pol,i,:] = smear_profile(dat[0,pol,nchan-i,:],smear)
            dat_s[0,pol,i,:] = smear_profile(dat[0,pol,i,:],smear)

        p0 = sub.get_Profile(pol,i)
        p1 = sub.get_Profile(pol,nchan-i)

        p0_new = p0.get_amps() - r*smear_profile(p1.get_amps(),smear)
        p1_new = p1.get_amps() - r*smear_profile(p0.get_amps(),smear)

        for ib in range(nbin):
            p0[ib] = float(p0_new[ib])
            p1[ib] = float(p1_new[ib])

arch.unload(fname + '.fix')

x = dat_s[0,0:2,:,:].ravel()
y = dat_f[0,0:2,:,:].ravel()
for i in range(len(x)):
    if abs(y[i]) > abs(x[i]):
        tmp = x[i]
        x[i] = y[i]
        y[i] = tmp

idx = numpy.where(x!=0.0)
x = x[idx]
y = y[idx]

m = 0.1*arange(1000.0)/1000.0
ss0 = 0.0*m
ss1 = 0.0*m
ss2 = 0.0*m
for i in range(len(m)):
    d = x*m[i] - y
    ss0[i] = numpy.sum(d > 0) - numpy.sum(d < 0)
    ss1[i] = numpy.abs(d).sum()
    ss2[i] = (d*d).sum()
