#! /usr/bin/env python

# Class to deal with indexing pulsar data files in an arbitrary
# directory structure.

import os
import sys
import fnmatch
from collections import namedtuple, OrderedDict
import sqlite3

# Note, need to be careful about setting/re-setting no_amps
# if this will be imported by other code that needs to load the
# data.  Could use "with" style context.
import psrchive
#psrchive.Profile.no_amps.fset(True)
class psrchive_no_amps(object):
    """Use this in with statements to temporarily change the
    PSRCHIVE no_amps setting.  Probably not thread-safe!"""
    def __init__(self,mode=True):
        self.mode = mode

    def __enter__(self):
        self.previous_setting = psrchive.Profile.no_amps.fget()
        psrchive.Profile.no_amps.fset(self.mode)

    def __exit__(self,t,v,tb):
        psrchive.Profile.no_amps.fset(self.previous_setting)


# dict of info to store and their sql type defs
_infotypes = OrderedDict()
_infotypes["fname"]   = "text unique" # file name 
_infotypes["path"]    = "text"        # path to file
_infotypes["source"]  = "text"        # source name
_infotypes["rcvr"]    = "text"        # receiver name
_infotypes["backend"] = "text"        # backend name
_infotypes["type"]    = "text"        # pulsar/cal/etc
_infotypes["mjd"]     = "real"        # MJD
_infotypes["bad"]     = "int"         # bad file flag
_infotypes["reason"]  = "text"        # reason for badness

_infofields = list(_infotypes.keys())

class PSRFile(namedtuple('PSRFile', _infofields)):
    """This class represents a single raw data file."""
    
    @classmethod
    def _fromfile(cls, fname_path):
        """Generate a PSRFile instance from a data file.  
        fname should be full path to file name."""
        (path,fname) = os.path.split(fname_path)
        try:
            with psrchive_no_amps():
                arch = psrchive.Archive_load(fname_path)
                source = arch.get_source()
                rcvr = arch.get_receiver_name()
                backend = arch.get_backend_name()
                type = arch.get_type()
                mjd = arch[0].get_epoch().in_days()
                bad = 0
                reason = ""
        except:
            source = "unk"
            rcvr = "unk"
            backend = "unk"
            type = "unk"
            mjd = 0.0
            bad = 1
            reason = "import error"
        return super(PSRFile,cls).__new__(cls,
                fname=fname, path=path, 
                source=source, rcvr=rcvr, backend=backend,
                type=type, mjd=mjd, bad=bad, reason=reason)

    @classmethod
    def _fromdb(cls, cursor, row):
        # Note, requires fields in db be in same order as in this class.
        # should be guaranteed if everything is done consistently 
        # via this interface..
        return cls._make(row)

    @property
    def full_path(self):
        return self.path + '/' + self.fname

class PSRIndex(object):
    """This class represents an index of pulsar data files."""

    def __init__(self, filename="index.db", create=False):

        if not create:
            if not os.path.exists(filename):
                raise RuntimeError("PSRIndex file '%s' not found" % filename)

        self.dbfilename = filename
        self.db = sqlite3.connect(self.dbfilename)
        self.db.row_factory = PSRFile._fromdb
        self.cur = self.db.cursor()
        create_qry = "create table if not exists files ("
        for f in _infofields:
            create_qry += f + " " + _infotypes[f] + ","
        create_qry = create_qry.rstrip(',') + ")"
        self.cur.execute(create_qry)
        self.verbose = False

        # These filters determine which files are considered for
        # inclusion.
        self.file_filters = [
                "guppi_*.fits",
                "puppi_*.fits",
                "vegas_*.fits",
                "5????.*.asp",
                "c??????.dat",
                "ABPP_*.ar",
                "*.[AB][CD]_????.ar",
                "*.[AB][CD]_????.cf",
                "*.[AB][CD][12]_????.ar",
                "*.[AB][CD][12]_????.cf",
                ]

    def list_files(self, basedir='.'):
        """Return a list of all matching files under the given 
        basedir."""
        basedir_full = os.path.abspath(basedir)
        out = []
        uniq_names = set()
        for (path, subdirs, fnames) in os.walk(basedir_full):
            for filter in self.file_filters:
                for fname in fnmatch.filter(fnames, filter):
                    if fname not in uniq_names:
                        uniq_names.add(fname)
                        out.append(os.path.join(path,fname))
                    else:
                        if self.verbose: 
                            print("Warning: file name collision %s" % fname)
        return out

    def add_file(self, fname_path, replace=False, commit=True):
        """Add a single file, given with full path, to the db.
        If file already exists in the db nothing will be done.
        If replace=True existing info will be overwritten."""
        if replace==False:
            (path,fname) = os.path.split(fname_path)
            self.cur.execute("select * from files where fname=?",(fname,))
            if self.cur.fetchone() != None: 
                # file exists
                if self.verbose: print("File exists: %s" % fname)
                return
        info = PSRFile._fromfile(fname_path)
        if self.verbose: print("Adding: %s" % info.fname)
        qry = "insert into files (" \
                + str.join(', ',_infofields) \
                + ") values (" \
                + str.join(', ',[':'+x for x in _infofields]) +")"
        self.cur.execute(qry, info._asdict())
        if commit: self.db.commit()

    def add_files(self, basedir='.'):
        for fname in self.list_files(basedir):
            self.add_file(fname, commit=False)
        self.db.commit()

    def flag_bad(self, fname, reason="", unflag=False):
        if unflag: badval=0
        else: badval=1
        qry = "update files set bad=?, reason=? where fname=?"
        self.cur.execute(qry, (badval, reason, fname))
        self.db.commit()

    def select(self, where=None, include_bad=False, as_dict=False):
        """Shortcut to select / fetchall"""
        qry = "select * from files"
        if (where is None) and include_bad:
            pass
        else:
            qry += " where "
            if not include_bad:
                qry += "not bad"
                if where is not None:
                    qry += " and (" + where + ")"
            else:
                qry += where
        qry += " order by mjd"
        if self.verbose: print(qry)
        self.cur.execute(qry)
        if as_dict:
            output = {}
            for f in self.cur.fetchall():
                output[f.fname] = f
            return output
        else:
            return self.cur.fetchall()
        

