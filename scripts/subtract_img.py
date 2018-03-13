#! /usr/bin/env python

import numpy
from numpy.fft import rfft, irfft
import psr_utils
import psrchive
import sys, os

#For Debugging
import matplotlib.pyplot as plt
#

def smear_profile(prof,fac):
    nb = len(prof)
    bmax = int(1.0/fac/2.0)
    if bmax>nb/2: bmax=nb/2
    fprof = rfft(prof)
    fprof[bmax:] = 0.0
    return irfft(fprof)

fname = sys.argv[1]
fullbase, ext = os.path.splitext(fname)
arch = psrchive.Archive_load(fname)
rcvr = arch.get_receiver_name()
arch.remove_baseline()
sub = arch[0]
epoch = str(sub.get_epoch()).split(":")[1].strip()
nchan = arch.get_nchan()
nbin = arch.get_nbin()
nsub = arch.get_nsubint()
dm = arch.get_dispersion_measure()
chbw = sub.get_bandwidth()/nchan

dat = arch.get_data()
dat_f = 0.0*dat
dat_s = 0.0*dat

datadir = os.path.dirname(os.path.realpath(__file__))
corrections = numpy.loadtxt(os.path.join(datadir,rcvr + '_imgrejcorrection.txt'),dtype={'names': ('MJD','Pol0','Pol1'),'formats':('S5','f4','f4')})
index = numpy.where(corrections['MJD'] == epoch)
pol0correction = corrections[index]['Pol0'][0]
pol1correction = corrections[index]['Pol1'][0]
#r = 0.00970*2.

if rcvr == "Rcvr_800":
  fcenter = 820.0
elif rcvr == "Rcvr1_2":
  fcenter = 1500.0

for n in range(0,nsub):
  sub = arch[n]
  for i in range(0,nchan):
    
    f0 = sub.get_centre_frequency(i)
    fwant = fcenter + fcenter - f0
    counterpart = False
    for j in range(nchan-1,0,-1):
      f1 = sub.get_centre_frequency(j)
      if f1 == fwant:
        counterpart = j
        break
#      print f1,fwant
    if counterpart == False:
      print "Didn't find counterpart frequency for %f" % f0
      sub.set_weight(i,0.0)
      continue
#    else:
#      print counterpart,f1
#    print f0, f1
#    sys.exit()
#    print f0,f1

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
        if pol == 0:
          correction = pol0correction/2.0
        else:
          correction = pol1correction/2.0
#        correction = correction * 16.0

        p0 = sub.get_Profile(pol,i)
        #p1 = sub.get_Profile(pol,nchan-i)
        p1 = sub.get_Profile(pol,j)

        p0_new = p0.get_amps() - smear_profile(correction*p1.get_amps(),smear)
##        if i == 128:
##          plt.title("%.2fMHz %.2fMHz" % (f0,f1))
##          plt.plot(p0_new,label='Corrected')
##          plt.plot(p0.get_amps(),label='Original')
##          plt.plot(smear_profile(correction*p1.get_amps(),smear),label='Model Image')
##          plt.show()
#        p1_new = p1.get_amps() - smear_profile(correction*p0.get_amps(),smear)
##        if i == 128:
##          plt.title("%.2fMHz %.2fMHz" % (f1,f0))
##          plt.plot(p1_new,label='Corrected')
##          plt.plot(p1.get_amps(),label='Original')
##          plt.plot(smear_profile(correction*p0.get_amps(),smear),label='Model Image')
##          plt.show()

        for ib in range(nbin):
            p0[ib] = float(p0_new[ib])
#            p1[ib] = float(p1_new[ib])

arch.unload(fullbase + '.imgrej')
