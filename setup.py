#!/usr/bin/env python

from distutils.core import setup

setup(name='nanopipe',
      version='1.2.2',
      description='NANOGrav calibration and TOA pipeline',
      author='Paul Demorest',
      author_email='pdemores@nrao.edu',
      url='http://github.com/demorest/nanopipe',
      packages=['nanopipe'],
      package_dir={'nanopipe': 'src'},
      package_data={'nanopipe': ['data/psrjnames.dat','data/psrbnames.dat']},
      scripts=['scripts/make_psr_make', 'scripts/update_be_delay',
          'scripts/get_proper_name', 'scripts/fix_receiver_name',
          'scripts/get_parfile_coords', 'scripts/psrindex']
     )
