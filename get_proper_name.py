#! /usr/bin/env python
import string

# load psrchive, set it to not load full data from the files
import psrchive

# Read in the name lists
datadir = '/data1/demorest/src/nanopipe' # TODO fix me up
psrbnames = map(string.rstrip,open(datadir+'/psrbnames.dat').readlines())
psrjnames = map(string.rstrip,open(datadir+'/psrjnames.dat').readlines())

# The list of official names
psrnames = [
    "J0218+4232",
    "J0613-0200",
    "J1012+5307",
    "J1024-0719",
    "J1455-3330",
    "J1600-3053",
    "J1614-2230",
    "J1643-1224",
    "J1713+0747",
    "J1721-2457",
    "J1730-2304",
    "J1744-1134",
    "J1751-2857",
    "J1801-1417",
    "B1802-07",
    "J1804-2717",
    "B1821-24",
    "J1829+2456",
    "J1843-1113",
    "J1903+0327",
    "J1909-3744",
    "J1911-1114",
    "J1918-0642",
    "B1937+21",
    "J2010-1323",
    "J2124-3358",
    "J2145-0750",
    ]

def proper_name(name):

    # Catch any special cases (eg known name errors) here
    if '0645+5150' in name:
        return 'J0645+5158'
    if '1910+1257' in name:
        return 'J1910+1256'
    if '1853+1308' in name:
        return 'J1853+1303'
    if '1949+31out' in name:
        return 'J1949+3106'

    # Look for a match in the lists
    for namelist in (psrbnames, psrjnames, psrnames):
        for psr in namelist:
            if psr.find(name) != -1:
                return psr

    # Fall back on orig name
    return name

def get_proper_name(filename):
    no_amps_bak = psrchive.Profile.no_amps.fget()
    psrchive.Profile.no_amps.fset(True)
    name_in_file = psrchive.Archive_load(filename).get_source().strip()
    psrchive.Profile.no_amps.fset(no_amps_bak)
    return proper_name(name_in_file)

if __name__=="__main__":
    import sys
    try:
        fname = sys.argv[1]
        print get_proper_name(fname)
    except:
        sys.exit(1)
