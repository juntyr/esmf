# This example demonstrates how to regrid between a GRIDSPEC grid and a tripole grid, both grids use masking.
# The grid files are required, they can be retrieved from the ESMF data repository:
#   wget http://www.earthsystemmodeling.org/download/data/GRIDSPEC_ACCESS1.nc
#   wget http://www.earthsystemmodeling.org/download/data/tx0.1v2_070911.nc

import ESMF
import numpy

# create a manager object with multiprocessor logging in debug mode
ESMF.Manager(logkind=ESMF.LogKind.MULTI, debug=True)

grid1 = "examples/data/GRIDSPEC_ACCESS1.nc"
grid2 = "examples/data/tx0.1v2_070911.nc"

# Create a  grid from a GRIDSPEC formatted file
grid = ESMF.Grid(filename=grid1, filetype=ESMF.FileFormat.GRIDSPEC,
                                add_corner_stagger=True, add_mask=True, varname="so")

# create a field on the center stagger locations of the source grid
srcfield = ESMF.Field(grid, 'srcfield', staggerloc=ESMF.StaggerLoc.CENTER, mask_values=[0])

# create a tripole grid
tripole = ESMF.Grid(filename=grid2, filetype=ESMF.FileFormat.SCRIP,
                    add_corner_stagger=True, add_mask=True, varname="grid_imask")

# create fields on the center stagger locations of the tripole grid
dstfield = ESMF.Field(tripole, 'dstfield', meshloc=ESMF.StaggerLoc.CENTER, mask_values=[0])
xctfield = ESMF.Field(tripole, 'xctfield', meshloc=ESMF.StaggerLoc.CENTER, mask_values=[0])

# create fields needed to analyze accuracy of conservative regridding
srcfracfield = ESMF.Field(grid, 'srcfracfield')
dstfracfield = ESMF.Field(tripole, 'dstfracfield')
srcareafield = ESMF.Field(grid, 'srcareafield')
dstareafield = ESMF.Field(tripole, 'dstareafield')

# get the coordinate pointers and set the coordinates
[lon,lat] = [0, 1]
gridXCoord = srcfield.grid.get_coords(lon, ESMF.StaggerLoc.CENTER)
gridYCoord = srcfield.grid.get_coords(lat, ESMF.StaggerLoc.CENTER)

deg2rad = 3.14159/180

srcfield.data[...] = 10.0 + (gridXCoord*deg2rad)**2 + (gridYCoord*deg2rad)**2

# get the coordinate pointers and set the coordinates
[lon,lat] = [0, 1]
gridXCoord = xctfield.grid.get_coords(lon, ESMF.StaggerLoc.CENTER)
gridYCoord = xctfield.grid.get_coords(lat, ESMF.StaggerLoc.CENTER)

xctfield.data[...] = 10.0 + (gridXCoord*deg2rad)**2 + (gridYCoord*deg2rad)**2

dstfield.data[...] = 1e20

# create an object to regrid data from the source to the destination field
# NOTE: this example requires the unmapped_action flag to be set to IGNORE missing values due to masking
regrid = ESMF.Regrid(srcfield, dstfield,
                     regrid_method=ESMF.RegridMethod.CONSERVE,
                     unmapped_action=ESMF.UnmappedAction.IGNORE,
                     src_mask_values=numpy.array([0]),
                     dst_mask_values=numpy.array([0]),
                     src_frac_field=srcfracfield,
                     dst_frac_field=dstfracfield)

# do the regridding from source to destination field
dstfield = regrid(srcfield, dstfield)

# calculate the area fields
srcareafield.get_area()
dstareafield.get_area()

csrverr = 0
srcmass = numpy.sum(numpy.abs(srcareafield.data * srcfracfield.data * srcfield.data))
dstmass = numpy.sum(numpy.abs(dstareafield.data * dstfield.data))
if dstmass is not 0:
    csrverr = numpy.abs(srcmass - dstmass) / dstmass

# compute the mean relative interpolation and conservation error
from operator import mul
num_nodes = reduce(mul, xctfield.shape)
relerr = 0
meanrelerr = 0
if num_nodes is not 0:
    ind = numpy.where((dstfield.data != 1e20) & (xctfield.data != 0) & (dstfracfield.data > .999))
    relerr = numpy.sum(numpy.abs(dstfield.data[ind]/dstfracfield.data[ind] - xctfield.data[ind]) / numpy.abs(xctfield.data[ind]))
    meanrelerr = relerr / num_nodes

# handle the parallel case
if ESMF.pet_count() > 1:
    try:
        from mpi4py import MPI
    except:
        raise ImportError
    comm = MPI.COMM_WORLD
    relerr = comm.reduce(relerr, op=MPI.SUM)
    num_nodes = comm.reduce(num_nodes, op=MPI.SUM)
    srcmass = comm.reduce(srcmass, op=MPI.SUM)
    dstmass = comm.reduce(dstmass, op=MPI.SUM)

# output the results from one processor only
if ESMF.local_pet() is 0:
    meanrelerr = relerr / num_nodes
    csrverr = numpy.abs(srcmass - dstmass) / dstmass

    print "ESMPy Tripole Regridding Example"
    print "  interpolation mean relative error = {}".format(meanrelerr)
    print "  mass conservation relative error  = {}".format(csrverr)