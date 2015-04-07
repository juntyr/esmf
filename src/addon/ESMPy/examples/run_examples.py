# $Id$

import os
import sys

import ESMF
import ESMF.api.constants as constants
from ESMF.test.regrid_from_file.run_regrid_from_file_dryrun import cache_data_file

parallel = False
if len(sys.argv) > 1:
    if "--parallel" in sys.argv[1]:
        parallel = True

# data files
datafilelist = ["ll1deg_grid.nc", "ll2.5deg_grid.nc", "mpas_uniform_10242_dual_counterclockwise.nc",
                "GRIDSPEC_ACCESS1.nc", "tx0.1v2_070911.nc", "T42_grid.nc"]

# Create data subdirectory if it doesn't exist.
datadir = "examples/data"
if not os.path.exists(datadir):
    os.mkdir(datadir)

# download the test files
if (ESMF.local_pet() == 0):
    for fname in datafilelist:
        # Retrieve the data files needed for the test cases from the remote server.
        status_ok = cache_data_file(os.path.join(datadir,fname))
        if not status_ok:
            raise IOError


# run utests, pipe to file
num_proc = 1
if parallel:
    # make sure we are not in uni mode
    if constants._ESMF_COMM == constants._ESMF_COMM_MPIUNI:
        raise ValueError("Cannot run parallel tests when ESMF is built with ESMF_COMM=mpiuni")

    # setup the constants
    num_proc = 4

if constants._ESMF_OS is constants._ESMF_OS_UNICOS:
    os.system("aprun -n "+str(num_proc)+" -a xt nosetests -vs --with-id -a '!slow' examples/exampletest.py")
else:
    if parallel:
        os.system("mpirun -np "+str(num_proc)+" nosetests -vs --with-id -a '!slow' examples/exampletest.py")
    else:
        os.system("nosetests -vs --with-id -a '!slow' examples/exampletest.py")