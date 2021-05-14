#! /usr/bin/env python

# Python implementation of (some of) psradd

import argparse
import psrchive

par = argparse.ArgumentParser()
par.add_argument("files", nargs='+')
par.add_argument("-j", dest="commands", action="append")
par.add_argument("-J", dest="scripts", action="append")
par.add_argument("-T", dest="tscrunch", action="store_true")
par.add_argument("-n", dest="fpatch", action="store_true")
par.add_argument("-o", dest="output", default="")
args = par.parse_args()

ta = psrchive.TimeAppend()
ta.chronological = True
# This isn't available right now..
#if args.fpatch:
#    fpatch = psrchive.PatchFrequency()
#else:
#    fpatch = None
fpatch = None

fa = psrchive.FrequencyAppend()
patch = psrchive.PatchTime()

# sort files by baseband
files = {}
for fname in args.files:
    bb = (fname.split('.')[-2]).split('_')[0]
    if not bb in files.keys():
        files[bb] = []
    files[bb].append(fname)

# TODO deal with fpatch

# Preprocessing and time dir first
tot = {}
for bb in files.keys():
    tot[bb] = None
    for fname in sorted(files[bb]):
        print("Processing '%s'" % fname)
        arch = psrchive.Archive_load(fname)

        # Preprocess: do commands then scripts
        if args.commands:
            for c in args.commands:
                print("  Command '%s'" % c)
                arch.execute(c)
        if args.scripts:
            for s in args.scripts:
                print("  Script '%s'" % s)
                for c in open(s).readlines():
                   arch.execute(c.rstrip('\n'))

        if tot[bb] is None:
            tot[bb] = arch.clone()
            ta.init(tot[bb])
        else:
            if fpatch is not None:
                fpatch.operate(tot[bb], arch)
            ta.append(tot[bb], arch)


# Freq dir
out = None
for bb in tot.keys():
    if out is None:
        out = tot[bb]
        fa.init(out)
    else:
        patch.operate(out,tot[bb])
        fa.append(out,tot[bb])

if args.tscrunch:
    out.tscrunch()

if args.output:
    outfname = args.output
else:
    outfname = "added.ar"

print("  Unload '%s'" % outfname)
out.unload(outfname)
