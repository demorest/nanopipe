#! /usr/bin/env python
import string

# load psrchive, set it to not load full data from the files
import psrchive

# Standardize Arecibo receiver names
def rcvr_name(orig_name):
    if orig_name == 'lbw': return 'L-wide'
    elif orig_name == 'sbw': return 'S-wide'
    else: return orig_name

def get_rcvr_name(filename):
    no_amps_bak = psrchive.Profile.no_amps.fget()
    psrchive.Profile.no_amps.fset(True)
    name_in_file = psrchive.Archive_load(filename).get_receiver_name().strip()
    psrchive.Profile.no_amps.fset(no_amps_bak)
    return rcvr_name(name_in_file)

if __name__=="__main__":
    import sys
    try:
        fname = sys.argv[1]
        print get_rcvr_name(fname)
    except:
        sys.exit(1)
