#! /usr/bin/env python

# Quick hack to make the DB tables for the 9-year data set.  With
# better advance planning this could have been automatically generated
# by make_psr_make..

import os
import re
import glob

import psrchive
psrchive.Profile.no_amps.fset(True)

class dbProfile(object):

    def __init__(self,fname):
        self.ProfileName = fname
        arch = psrchive.Archive_load(fname)
        self.n_subbands = arch.get_nchan()
        self.n_dumps = arch.get_nsubint()
        self.dump_length = arch[0].get_duration()
        self.subbands_width = abs(arch.get_bandwidth()) / arch.get_nchan()
        self.format = 'PSRFITS'
        self.sourceRawProfileName = ""
        self.sourceProfileName = ""
        self.processingType = ""
        self.processingFileName = ""
        if '.calib' in fname:
            cal_files = arch.execute('e hist:cal_file').split('=')[-1].rstrip()
            if cal_files != 'NONE':
                for f in cal_files.split(): self.add_source(f)

    def add_source(self,fname):
        """Add a filename to list of source profiles."""
        # Keep this as a string for now, could store internally as a list
        if self.sourceProfileName == "":
            self.sourceProfileName = fname
        else:
            self.sourceProfileName += ',' + fname

    def add_raw_source(self,fname):
        """Add a filename to list of raw source profiles."""
        # Keep this as a string for now, could store internally as a list
        if self.sourceRawProfileName == "":
            self.sourceRawProfileName = fname
        else:
            self.sourceRawProfileName += ',' + fname

    def loading_info(self):
        """Return the profile loading info as a string."""
        rv = ""
        for thing in ['ProfileName', 'n_subbands', 'subbands_width',
                'n_dumps', 'dump_length', 'format', 'sourceRawProfileName',
                'sourceProfileName', 'processingType', 'processingFileName']:
            rv += thing + ': ' + str(getattr(self,thing)) + '\n'
        return rv


# File extensions to consider
exts = ['rf','cf','ff','norm','zap','calib']

# extension of raw files
rawext = 'fits'

# Version tag
ver = '9y'

scan_re = re.compile('(.+)\.'+ver+'\.(.+)$')

for ext in exts:
    fnames = glob.glob('*.%s.*%s' % (ver,ext))
    for fname in fnames:
        base = os.path.splitext(fname)[0]
        scan_m = scan_re.match(fname)
        if scan_m:
            scan = scan_m.group(1)
            fullext = scan_m.group(2)
            d = dbProfile(fname)

            # Source raw profiles
            if ext == 'cf':
                d.add_raw_source(scan+'.'+rawext)
            else:
                for rawf in sorted(glob.glob(scan+'_????.'+rawext)):
                    d.add_raw_source(rawf)

            # Details for each file type:

            if ext == 'rf':
                d.processingType = 'tscrunch'
                d.processingFileName = 'initial_tscrunch.%s.txt' % (ver,)

            elif ext == 'cf':
                d.processingType = 'tscrunch'
                d.processingFileName = 'cal_tscrunch.%s.txt' % (ver,)

            elif ext == 'calib':
                d.processingType = 'polcal'
                caltype = fullext[0]
                d.processingFileName = 'polcal_%s.%s.txt' % (caltype,ver)
                d.add_source(scan + '.rf')

            elif ext == 'zap':
                d.processingType = 'zap'
                d.processingFileName = 'rfizap.%s.txt' % (ver,)
                d.add_source(base + '.calib')

            elif ext == 'norm':
                d.processingType = 'normalize'
                d.processingFileName = 'normalize.%s.txt' % (ver,)
                d.add_source(base + '.zap')

            elif ext == 'ff':
                d.processingType = 'fscrunch,tscrunch'
                d.processingFileName = \
                        'final_fscrunch.%s.txt,final_tscrunch.%s.txt' % (ver,
                                ver)
                d.add_source(base + '.zap')

            print d.loading_info() 




