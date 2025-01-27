"""
regrid unit test file
"""

import pytest

import os

from esmpy import *
from esmpy.test.base import TestBase
from esmpy.api.constants import _ESMF_NETCDF, _ESMF_PIO
from esmpy.util.field_utilities import compare_fields
from esmpy.util.grid_utilities import *
from esmpy.util.mesh_utilities import *
from esmpy.util.cache_data import DATA_DIR


class TestRegrid(TestBase):

    def run_regridding(srcfield, dstfield, srcfracfield, dstfracfield):
        # This is for documentation. Do not modify.
        '''
        PRECONDITIONS: Two Fields have been created and a regridding
                       operation is desired from 'srcfield' to 'dstfield'.
                       The 'srcfracfield' and 'dstfractfield' are Fields
                       created to hold the fractions of the source and
                       destination fields which contribute to conservative
                       regridding.\n
        POSTCONDITIONS: A regridding operation has set the data on
                        'dstfield', 'srcfracfield', and 'dstfracfield'.\n
        RETURN VALUES: \n Field :: dstfield \n
                          Field :: srcfracfield \n
                          Field :: dstfracfield \n
        '''
        # call the regridding functions
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    regrid_method=esmpy.RegridMethod.CONSERVE,
                                    unmapped_action=esmpy.UnmappedAction.ERROR,
                                    src_frac_field=srcfracfield,
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        return dstfield, srcfracfield, dstfracfield

    def test_field_regrid(self):
        # create grids
        max_index = np.array([20, 20])
        srcgrid = Grid(max_index, coord_sys=CoordSys.CART)
        max_index = np.array([25, 25])
        dstgrid = Grid(max_index, coord_sys=CoordSys.CART)

        # Add coordinates
        srcgrid.add_coords()
        dstgrid.add_coords()

        [x, y] = [0, 1]
        gridXCorner = srcgrid.get_coords(x)
        gridYCorner = srcgrid.get_coords(y)

        for i in range(gridXCorner.shape[x]):
            gridXCorner[i, :] = float(i) / 6.

        for j in range(gridYCorner.shape[y]):
            gridYCorner[:, j] = float(j) / 6.

        gridXCorner = dstgrid.get_coords(x)
        gridYCorner = dstgrid.get_coords(y)

        for i in range(gridXCorner.shape[x]):
            gridXCorner[i, :] = float(i) / 4.

        for j in range(gridYCorner.shape[y]):
            gridYCorner[:, j] = float(j) / 4.

        # create a Field on the Grid
        srcfield = Field(srcgrid)
        srcfield.data[:, :] = 10.
        dstfield = Field(srcgrid)
        dstfield.data[:, :] = 10.

        # regridding
        rh = Regrid(srcfield, dstfield, regrid_method=RegridMethod.BILINEAR,
                    line_type=LineType.CART, factors=False)
        _ = rh(srcfield, dstfield)

    @pytest.mark.skipif(not constants._ESMF_USE_INMEM_FACTORS, reason="compiler does not support in-memory weights")
    @pytest.mark.skipif(pet_count()!=1, reason="test must be run in serial")
    def test_field_regrid_factor_retrieval(self):
        # Test retrieving factors from a route handle.

        for offset in [0, 1000]:

            max_index = np.array([2, 2])
            srcgrid = Grid(max_index, coord_sys=CoordSys.CART)

            max_index = np.array([20, 20])
            dstgrid = Grid(max_index, coord_sys=CoordSys.CART)

            srcgrid.add_coords()
            dstgrid.add_coords()

            [x, y] = [0, 1]

            # Source grid creation ============================================

            xcoords = srcgrid.get_coords(x)
            ycoords = srcgrid.get_coords(y)

            for i in range(xcoords.shape[x]):
                xcoords[i, :] = float(i) / 6.

            for j in range(ycoords.shape[y]):
                ycoords[:, j] = float(j) / 6.

            # Destination grid creation =======================================

            xcoords = dstgrid.get_coords(x)
            ycoords = dstgrid.get_coords(y)

            for i in range(xcoords.shape[x]):
                xcoords[i, :] = float(i) / 6. + offset

            for j in range(ycoords.shape[y]):
                ycoords[:, j] = float(j) / 6. + offset

            # Initialize field data ===========================================

            srcfield = Field(srcgrid)
            srcfield.data[:, :] = 10.

            dstfield = Field(dstgrid)
            dstfield.data[:, :] = -999.

            # Test factor creation with and without deep copying ==============

            keywords = dict(deep_copy=[False, True], as_dict=[False, True])
            for k in self.iter_product_keywords(keywords):
                rh = Regrid(srcfield, dstfield,
                            regrid_method=RegridMethod.BILINEAR,
                            line_type=LineType.CART, factors=True,
                            create_rh=False,
                            unmapped_action=UnmappedAction.IGNORE)
                _ = rh(srcfield, dstfield)

                fl, fil, fdict = [None] * 3  # Reset at each loop

                if k.as_dict:
                    fdict = rh.get_weights_dict(deep_copy=k.deep_copy)
                    fl = fdict['weights']
                    fil = np.zeros((fl.shape[0], 2), dtype=np.int32)
                    fil[:, 0] = fdict['col_src']
                    fil[:, 1] = fdict['row_dst']
                else:
                    fl, fil = rh.get_factors(deep_copy=k.deep_copy)

                if k.deep_copy:
                    self.assertNotEqual(id(fl), id(rh._factor_list))
                else:
                    self.assertEqual(id(fl), id(rh._factor_list))

                # Offset is added to the destination coordinates to test for
                # disjoint grids and factor list retrieval. When grids are
                # disjoint and the unmapped action is to ignore, there should
                # be zero rows in the returned arrays.
                if offset == 0:
                    self.assertEqual(fl.shape, (16,))
                    desired = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0,
                               0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
                    self.assertNumpyAllClose(fl, np.array(desired,
                                                          dtype=np.float64))

                    self.assertEqual(fil.shape, (16, 2))
                    desired = [[1, 1], [2, 1], [3, 1], [4, 1], [1, 2], [2, 2],
                               [3, 2], [4, 2], [1, 21], [2, 21], [3, 21],
                               [4, 21], [1, 22], [2, 22], [3, 22], [4, 22]]
                    desired = np.array(desired, dtype=np.int32)
                    self.assertNumpyAll(fil, desired)
                else:
                    self.assertEqual(fl.shape, (0,))
                    self.assertEqual(fil.shape, (0, 2))

                rh.destroy()

    @pytest.mark.skipif(_ESMF_PIO==False, reason="PIO required in ESMF build")
    @pytest.mark.skipif(_ESMF_NETCDF==False, reason="NetCDF required in ESMF build")
    def test_field_regrid_file1(self):
        mgr = Manager()

        # Create grids.
        nx = 20
        ny = 24
        max_index = np.array([nx, ny])
        srcgrid = Grid(max_index, coord_sys=CoordSys.CART)
        dstgrid = Grid(max_index, coord_sys=CoordSys.CART)

        grids = [srcgrid, dstgrid]
        # Allocate coordinate arrays.
        for grid in grids:
            grid.add_coords()

        # Adjust x-coordinates by a rank offset.
        x_coords = np.arange(1, srcgrid.size[0][0] + 1) + 10 * (local_pet() + 1)
        # Adjust y-coordinates by a constant offset.
        y_coords = np.arange(1, ny + 1) + 100
        y_coords, x_coords = np.meshgrid(y_coords, x_coords)

        # Fill each grid's coordinate arrays.
        for grid in [srcgrid, dstgrid]:
            grid.get_coords(0)[:] = x_coords
            grid.get_coords(1)[:] = y_coords

        # Create the fields on the grids and fill the data values.
        srcfield = Field(srcgrid)
        srcfield.data[:, :] = 10.
        dstfield = Field(dstgrid)
        dstfield.data[:, :] = 20.

        # Check for and remove the test file if it exists.
        filename = "esmpy_test_field_regrid_file.nc"
        if local_pet() == 0:
            path = os.path.join(os.getcwd(), filename)
            if os.path.isfile(path):
                os.remove(path)
        mgr.barrier()

        # Execute regridding from file.
        _ = Regrid(srcfield, dstfield, filename=filename, large_file=True)
        mgr.barrier()

        # Test weight file contents are rational.
        if local_pet() == 0:
            self.assertWeightFileIsRational(filename, 480, 480)
        mgr.barrier()

        if local_pet() == 0:
            if os.path.isfile(path):
                os.remove(path)

    @pytest.mark.skipif(_ESMF_PIO==False, reason="PIO required in ESMF build")
    @pytest.mark.skipif(_ESMF_NETCDF==False, reason="NetCDF required in ESMF build")
    def test_field_regrid_file2(self):
        mgr = Manager()
        filename = 'esmpy_test_field_regrid_file2.nc'
        if local_pet() == 0:
            path = os.path.join(os.getcwd(), filename)
            if os.path.isfile(path):
                os.remove(path)
        mgr.barrier()
        
        srcgrid = esmpy.Grid(np.array([20, 20]),
                            staggerloc=esmpy.StaggerLoc.CENTER,
                            coord_sys=esmpy.CoordSys.SPH_DEG)

        # Get and set the source grid coordinates.
        srcGridCoordLon = srcgrid.get_coords(0)
        srcGridCoordLat = srcgrid.get_coords(1)

        lons = np.linspace(-120, 120, 20)
        lats = np.linspace(-60, 60, 20)
        
        # parallel coordinates
        slons_par = lons[srcgrid.lower_bounds[esmpy.StaggerLoc.CENTER][0]:srcgrid.upper_bounds[esmpy.StaggerLoc.CENTER][0]]
        slats_par = lats[srcgrid.lower_bounds[esmpy.StaggerLoc.CENTER][1]:srcgrid.upper_bounds[esmpy.StaggerLoc.CENTER][1]]
        
        # make sure to use indexing='ij' as ESMPy backend uses matrix indexing (not Cartesian)
        lonm, latm = np.meshgrid(slons_par, slats_par, indexing='ij')
        
        srcGridCoordLon[:] = lonm
        srcGridCoordLat[:] = latm

        dstgrid = esmpy.Grid(np.array([10, 10]),
                             staggerloc=esmpy.StaggerLoc.CENTER,
                             coord_sys=esmpy.CoordSys.SPH_DEG)

        # Get and set the source grid coordinates.
        dstGridCoordLon = dstgrid.get_coords(0)
        dstGridCoordLat = dstgrid.get_coords(1)
        
        lons = np.linspace(-120, 120, 10)
        lats = np.linspace(-60, 60, 10)

        # parallel coordinates
        dlons_par = lons[dstgrid.lower_bounds[esmpy.StaggerLoc.CENTER][0]:dstgrid.upper_bounds[esmpy.StaggerLoc.CENTER][0]]
        dlats_par = lats[dstgrid.lower_bounds[esmpy.StaggerLoc.CENTER][1]:dstgrid.upper_bounds[esmpy.StaggerLoc.CENTER][1]]
        
        # make sure to use indexing='ij' as ESMPy backend uses matrix indexing (not Cartesian)
        lonm, latm = np.meshgrid(dlons_par, dlats_par, indexing='ij')
        
        dstGridCoordLon[:] = lonm
        dstGridCoordLat[:] = latm

        srcfield = esmpy.Field(srcgrid)
        dstfield = esmpy.Field(dstgrid)

        _ = esmpy.Regrid(srcfield, dstfield, filename=filename,
                        regrid_method=esmpy.RegridMethod.BILINEAR,
                        unmapped_action=esmpy.UnmappedAction.IGNORE)
        mgr.barrier()

        self.assertTrue(os.path.exists(filename))

        src_size = 400
        dst_size = 100
        self.assertWeightFileIsRational(filename, src_size, dst_size)
        mgr.barrier()

        if local_pet() == 0:
            if os.path.isfile(path):
                os.remove(path)

    @pytest.mark.skipif(_ESMF_PIO==False, reason="PIO required in ESMF build")
    @pytest.mark.skipif(_ESMF_NETCDF==False, reason="NetCDF required in ESMF build")
    # remove this test for 8.2.0 due to unexplained segv
    def _field_regrid_file_withaux(self):

        mgr = Manager()
        filename = 'esmpy_test_field_regrid_withaux.nc'
        if local_pet() == 0:
            path = os.path.join(os.getcwd(), filename)
            if os.path.isfile(path):
                os.remove(path)
        mgr.barrier()


        grid1 = os.path.join(DATA_DIR, "ll2.5deg_grid.nc")
        srcgrid = esmpy.Grid(filename=grid1, filetype=esmpy.FileFormat.SCRIP, add_corner_stagger=True)

        grid2 = os.path.join(DATA_DIR, "T42_grid.nc")
        dstgrid = esmpy.Grid(filename=grid2, filetype=esmpy.FileFormat.SCRIP, add_corner_stagger=True)

        srcfield = esmpy.Field(srcgrid)
        dstfield = esmpy.Field(dstgrid)

        _ = esmpy.Regrid(srcfield, dstfield, filename=filename,
                        regrid_method=esmpy.RegridMethod.BILINEAR,
                        unmapped_action=esmpy.UnmappedAction.IGNORE,
                        filemode=esmpy.FileMode.WITHAUX,
                        src_file=grid1, dst_file=grid2,
                        src_file_type=esmpy.FileFormat.SCRIP,
                        dst_file_type=esmpy.FileFormat.SCRIP)
        mgr.barrier()

        self.assertTrue(os.path.exists(filename))

        src_size = 10368
        dst_size = 8192
        self.assertWeightFileIsRational(filename, src_size, dst_size)
        mgr.barrier()

        # Confirm auxiliary variables exist in the file
        try:
            from netCDF4 import Dataset
        except ImportError:
            pass
        else:
            ds = Dataset(filename)
            try:
                vars = ds.variables.keys()
                try:
                    self.assertGreater(len(vars), 3)
                except AssertionError:
                    print(vars)
                    raise
            finally:
                ds.close()

        if local_pet() == 0:
            if os.path.isfile(path):
                os.remove(path)

    @pytest.mark.skipif(_ESMF_PIO==False, reason="PIO required in ESMF build")
    @pytest.mark.skipif(_ESMF_NETCDF==False, reason="NetCDF required in ESMF build")
    def test_field_regrid_file3(self):
        mgr = Manager()
        filename = 'esmpy_test_field_from_file.nc'
        path = os.path.join(os.getcwd(), filename)
        if local_pet() == 0:
            path = os.path.join(os.getcwd(), filename)
            if os.path.isfile(path):
                os.remove(path)
        mgr.barrier()

        srcgrid = esmpy.Grid(np.array([20, 20]),
                            staggerloc=esmpy.StaggerLoc.CENTER,
                            coord_sys=esmpy.CoordSys.CART)

        # Get and set the source grid coordinates.
        srcGridCoordLon = srcgrid.get_coords(0)
        srcGridCoordLat = srcgrid.get_coords(1)

        lons = np.linspace(-120, 120, 20)
        lats = np.linspace(-60, 60, 20)

        # parallel coordinates
        slons_par = lons[srcgrid.lower_bounds[esmpy.StaggerLoc.CENTER][0]:srcgrid.upper_bounds[esmpy.StaggerLoc.CENTER][0]]
        slats_par = lats[srcgrid.lower_bounds[esmpy.StaggerLoc.CENTER][1]:srcgrid.upper_bounds[esmpy.StaggerLoc.CENTER][1]]

        # make sure to use indexing='ij' as ESMPy backend uses matrix indexing (not Cartesian)
        lonm, latm = np.meshgrid(slons_par, slats_par, indexing='ij')

        srcGridCoordLon[:] = lonm
        srcGridCoordLat[:] = latm

        dstgrid = esmpy.Grid(np.array([10, 10]),
                             staggerloc=esmpy.StaggerLoc.CENTER,
                             coord_sys=esmpy.CoordSys.CART)

        # Get and set the source grid coordinates.
        dstGridCoordLon = dstgrid.get_coords(0)
        dstGridCoordLat = dstgrid.get_coords(1)

        lons = np.linspace(-120, 120, 10)
        lats = np.linspace(-60, 60, 10)

        # parallel coordinates
        dlons_par = lons[dstgrid.lower_bounds[esmpy.StaggerLoc.CENTER][0]:dstgrid.upper_bounds[esmpy.StaggerLoc.CENTER][0]]
        dlats_par = lats[dstgrid.lower_bounds[esmpy.StaggerLoc.CENTER][1]:dstgrid.upper_bounds[esmpy.StaggerLoc.CENTER][1]]

        # make sure to use indexing='ij' as ESMPy backend uses matrix indexing (not Cartesian)
        lonm, latm = np.meshgrid(dlons_par, dlats_par, indexing='ij')

        dstGridCoordLon[:] = lonm
        dstGridCoordLat[:] = latm


        srcfield = esmpy.Field(srcgrid)
        dstfield = esmpy.Field(dstgrid)
        xctfield = esmpy.Field(dstgrid)

        srcfield.data[:,:] = 24
        xctfield.data[:,:] = 24
        dstfield.data[:,:] = 0

        self.assertTrue(np.all(srcfield.data[:,:] == 24))
        self.assertTrue(np.all(dstfield.data[:,:] == 0))

        regridS2D = esmpy.Regrid(srcfield, dstfield, filename=filename,
                        regrid_method=esmpy.RegridMethod.BILINEAR,
                        unmapped_action=esmpy.UnmappedAction.ERROR,
                        create_rh=True,
                        ignore_degenerate=False)
        mgr.barrier()

        self.assertTrue(os.path.exists(filename))

        self.assertTrue(np.all(srcfield.data[:,:] == 24))
        self.assertNumpyAllClose(xctfield.data, dstfield.data)

        regridS2D = esmpy.RegridFromFile(srcfield, dstfield, filename)
        mgr.barrier()

        self.assertTrue(np.all(srcfield.data[:,:] == 24))
        self.assertNumpyAllClose(xctfield.data, dstfield.data)

        destfield = regridS2D(srcfield, dstfield)

        self.assertWeightFileIsRational(filename, 20*20, 10*10)
        self.assertTrue(np.all(srcfield.data[:,:] == 24))
        self.assertNumpyAllClose(xctfield.data, dstfield.data)
        mgr.barrier()

        if local_pet() == 0:
            if os.path.isfile(path):
                os.remove(path)

    def test_field_regrid_file4(self):
        mgr = Manager()
        filename = 'routehandlefile.nc'
        path = os.path.join(os.getcwd(), filename)
        if local_pet() == 0:
            path = os.path.join(os.getcwd(), filename)
            if os.path.isfile(path):
                os.remove(path)
        mgr.barrier()

        srcgrid = esmpy.Grid(np.array([20, 20]),
                            staggerloc=esmpy.StaggerLoc.CENTER,
                            coord_sys=esmpy.CoordSys.CART)

        # Get and set the source grid coordinates.
        srcGridCoordLon = srcgrid.get_coords(0)
        srcGridCoordLat = srcgrid.get_coords(1)

        lons = np.linspace(-120, 120, 20)
        lats = np.linspace(-60, 60, 20)

        # parallel coordinates
        slons_par = lons[srcgrid.lower_bounds[esmpy.StaggerLoc.CENTER][0]:srcgrid.upper_bounds[esmpy.StaggerLoc.CENTER][0]]
        slats_par = lats[srcgrid.lower_bounds[esmpy.StaggerLoc.CENTER][1]:srcgrid.upper_bounds[esmpy.StaggerLoc.CENTER][1]]

        # make sure to use indexing='ij' as ESMPy backend uses matrix indexing (not Cartesian)
        lonm, latm = np.meshgrid(slons_par, slats_par, indexing='ij')

        srcGridCoordLon[:] = lonm
        srcGridCoordLat[:] = latm

        dstgrid = esmpy.Grid(np.array([10, 10]),
                             staggerloc=esmpy.StaggerLoc.CENTER,
                             coord_sys=esmpy.CoordSys.CART)

        # Get and set the source grid coordinates.
        dstGridCoordLon = dstgrid.get_coords(0)
        dstGridCoordLat = dstgrid.get_coords(1)

        lons = np.linspace(-120, 120, 10)
        lats = np.linspace(-60, 60, 10)

        # parallel coordinates
        dlons_par = lons[dstgrid.lower_bounds[esmpy.StaggerLoc.CENTER][0]:dstgrid.upper_bounds[esmpy.StaggerLoc.CENTER][0]]
        dlats_par = lats[dstgrid.lower_bounds[esmpy.StaggerLoc.CENTER][1]:dstgrid.upper_bounds[esmpy.StaggerLoc.CENTER][1]]

        # make sure to use indexing='ij' as ESMPy backend uses matrix indexing (not Cartesian)
        lonm, latm = np.meshgrid(dlons_par, dlats_par, indexing='ij')

        dstGridCoordLon[:] = lonm
        dstGridCoordLat[:] = latm


        srcfield = esmpy.Field(srcgrid)
        dstfield = esmpy.Field(dstgrid)
        xctfield = esmpy.Field(dstgrid)

        srcfield.data[:,:] = 24
        xctfield.data[:,:] = 24
        dstfield.data[:,:] = 0

        self.assertTrue(np.all(srcfield.data[:,:] == 24))
        self.assertTrue(np.all(dstfield.data[:,:] == 0))

        regridS2D = esmpy.Regrid(srcfield, dstfield,
                        rh_filename=filename,
                        regrid_method=esmpy.RegridMethod.BILINEAR,
                        unmapped_action=esmpy.UnmappedAction.ERROR,
                        create_rh=True,
                        ignore_degenerate=False)
        mgr.barrier()

        self.assertTrue(os.path.exists(filename))

        self.assertTrue(np.all(srcfield.data[:,:] == 24))
        self.assertNumpyAllClose(xctfield.data, dstfield.data)

        regridS2D = esmpy.RegridFromFile(srcfield, dstfield, rh_filename=filename)
        mgr.barrier()

        self.assertTrue(np.all(srcfield.data[:,:] == 24))
        self.assertNumpyAllClose(xctfield.data, dstfield.data)

        destfield = regridS2D(srcfield, dstfield)

        # self.assertWeightFileIsRational(filename, 20*20, 10*10)
        self.assertTrue(np.all(srcfield.data[:,:] == 24))
        self.assertNumpyAllClose(xctfield.data, dstfield.data)
        mgr.barrier()

        if local_pet() == 0:
            if os.path.isfile(path):
                os.remove(path)

    @pytest.mark.skipif(pet_count() not in {1, 4}, reason="test requires 1 or 4 cores")
    def test_field_regrid_gridmesh(self):
        mesh = None
        if pet_count() == 4:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn, _ = \
                mesh_create_50()
        dstfield = Field(mesh, meshloc=MeshLoc.ELEMENT)

        # create grid
        max_index = np.array([16, 16])
        grid = Grid(max_index, coord_sys=CoordSys.CART)

        # Add coordinates
        grid.add_coords(staggerloc=[StaggerLoc.CENTER, StaggerLoc.CORNER])

        [x, y] = [0, 1]
        gridXCorner = grid.get_coords(x, staggerloc=StaggerLoc.CORNER)
        gridYCorner = grid.get_coords(y, staggerloc=StaggerLoc.CORNER)

        for i in range(gridXCorner.shape[x]):
            gridXCorner[i, :] = float(i)

        for j in range(gridYCorner.shape[y]):
            gridYCorner[:, j] = float(j)

        # create a Field on the Grid
        srcfield = Field(grid)

        srcfield.data[:, :] = 10.

        # regridding
        rh = Regrid(srcfield, dstfield, regrid_method=RegridMethod.CONSERVE)
        dstfield = rh(srcfield, dstfield)

    @pytest.mark.skipif(pet_count() not in {1, 4}, reason="test requires 1 or 4 cores")
    def test_field_regrid_zeroregion(self):
        mesh = None
        if pet_count() == 4:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn, _ = \
                mesh_create_50()

        # create a field on the mesh
        srcfield = Field(mesh, meshloc=MeshLoc.ELEMENT)

        # initialize the source field
        for i in range(srcfield.data.shape[0]):
            srcfield.data[i] = 20.0

        # create grid
        grid = grid_create_from_bounds([0, 4], [0, 4], 8, 8, corners=True, domask=True)

        [x, y] = [0, 1]

        # create a Field on the Grid
        dstfield = Field(grid)

        # initialize the destination field according to the mask
        dstfield.data[:, :] = -100

        # regridding
        rh = Regrid(srcfield, dstfield, regrid_method=RegridMethod.CONSERVE,
                    dst_mask_values=np.atleast_1d(np.array([0])))
        dstfield = rh(srcfield, dstfield, zero_region=Region.SELECT)

        # validate that the masked values were not zeroed out
        for i in range(dstfield.data.shape[x]):
            for j in range(dstfield.data.shape[y]):
                if dstfield.grid.mask[StaggerLoc.CENTER][i, j] == 0:
                    assert(dstfield[i, j] == 0)

    @pytest.mark.skipif(_ESMF_PIO==False, reason="PIO required in ESMF build")
    @pytest.mark.skipif(_ESMF_NETCDF==False, reason="NetCDF required in ESMF build")
    def test_field_regrid_zeroregion_select_ndbounds(self):
        # Test zero region select during a sparse matrix multiplication
        # having undistributed dimensions.

        # Create source field and mask some elements
        srcgrid = grid_create_from_bounds([0, 4], [0, 4], 240, 240, corners=False,
                                          domask=True)
        srcfield = Field(srcgrid, ndbounds=[3])
        srcfield.data[:] = 33.33
        srcmask = srcgrid.get_item(GridItem.MASK)
        srcmask[3:30, 10:40] = 0

        # Create the destination field without a mask
        dstgrid = grid_create_from_bounds([0, 4], [0, 4], 80, 80, corners=False,
                                          domask=False)
        dstfield = Field(dstgrid, ndbounds=[3])
        dstfield.data[:] = -999

        # Regrid in-memory
        rh = Regrid(srcfield, dstfield, regrid_method=RegridMethod.BILINEAR,
                    src_mask_values=np.atleast_1d(np.array([0])),
                    dst_mask_values=np.atleast_1d(np.array([0])),
                    unmapped_action=UnmappedAction.IGNORE)
        _ = rh(srcfield, dstfield, zero_region=Region.SELECT)

        # Assert fill values are retained
        self.assertGreater(np.sum(dstfield.data == 33.33), 10)
        self.assertGreater(np.sum(dstfield.data == -999), 10)

        # Write the regridding operation weights to file
        dstfield.data[:] = -999
        filename = os.path.join(DATA_DIR, '_esmf_test_weights_.nc')
        _ = Regrid(srcfield, dstfield, regrid_method=RegridMethod.BILINEAR,
                   src_mask_values=np.atleast_1d(np.array([0])),
                   unmapped_action=UnmappedAction.IGNORE,
                   filename=filename)
        self.assertTrue(np.all(dstfield.data == -999))

        # Compute the regrid from file route handle
        rh2 = RegridFromFile(srcfield, dstfield, filename=filename)
        self.assertTrue(np.all(dstfield.data == -999))
        dstfield = rh2(srcfield, dstfield, zero_region=esmpy.Region.SELECT)

        # Assert fill values are retained
        self.assertGreater(np.sum(dstfield.data == 33.33), 10)
        self.assertGreater(np.sum(dstfield.data == -999), 10)

        if (esmpy.local_pet() == 0):
            if os.path.exists(filename):
                os.remove(filename)

    @pytest.mark.skipif(pet_count() not in {1, 4}, reason="test requires 1 or 4 cores")
    def test_field_regrid_area(self):
        mesh = None
        if pet_count() == 4:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn, _ = \
                mesh_create_50()

        # create grid
        grid = grid_create_from_bounds([0, 4], [0, 4], 8, 8, corners=True, doarea=True)

        [x, y] = [0, 1]

        # create area field
        dstarea = Field(mesh, name='DESTINATION AREAS!',
                           meshloc=MeshLoc.ELEMENT)
        dstarea.get_area()

        # create a Field on the Grid
        srcarea = Field(grid, name="SOURCE AREAS!")
        srcarea.get_area()

        for i in range(srcarea.data.shape[x]):
            for j in range(srcarea.data.shape[y]):
                if (srcarea.data[i, j] != 5):
                    print ("Cell area is {0}, but expected 5".format(srcarea[i, j]))

        # subtract two because the last two cells of mesh are triangles with half area
        for i in range(dstarea.data.shape[0]):
            if (dstarea.data[i] != 0.25):
                assert (dstarea.data[i] == 0.125)

    def test_field_regrid_periodic(self):
        # create a grid
        srcgrid = grid_create_from_bounds_periodic(60, 30, corners=True, domask=True)
        dstgrid = grid_create_from_bounds_periodic(55, 28, corners=True)

        # create the Fields
        srcfield = esmpy.Field(srcgrid, name='srcfield')
        dstfield = esmpy.Field(dstgrid, name='dstfield')
        exactfield = esmpy.Field(dstgrid, name='exactfield')

        # create the fraction fields
        srcfracfield = esmpy.Field(srcgrid, name='srcfracfield')
        dstfracfield = esmpy.Field(dstgrid, name='dstfracfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_grid_periodic(srcfield)
        exact_field = initialize_field_grid_periodic(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    src_mask_values=np.atleast_1d(np.array([0])),
                                    regrid_method=esmpy.RegridMethod.CONSERVE,
                                    unmapped_action=esmpy.UnmappedAction.ERROR,
                                    src_frac_field=srcfracfield,
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_grid(srcfield,
                                    dofrac=True, fracfield=srcfracfield)
        dstmass = compute_mass_grid(dstfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, exact_field, 
                                                   10E-2, 10E-2, 10e-15, 
                                                   dstfracfield=dstfracfield,
                                                   mass1=srcmass, mass2=dstmass)

        self.assertAlmostEqual(meanrel, 0.0016447124122954575)
        self.assertAlmostEqual(csrvrel, 0.0)

    def test_grid_grid_3d_bilinear_cartesian(self):
        # RO: This test creates the same Grid on every processor, it could be improved

        # create a grid
        srcgrid = grid_create_from_bounds_3d([0, 21], [0, 21], [0, 21], 21, 21, 21, corners=False)
        dstgrid = grid_create_from_bounds_3d([0.5, 19.5], [0.5, 19.5], [0.5, 19.5], 19, 19, 19, corners=False)

        # create Field objects on the Meshes
        srcfield = esmpy.Field(srcgrid, name='srcfield')
        dstfield = esmpy.Field(dstgrid, name='dstfield')
        exactfield = esmpy.Field(dstgrid, name='exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_grid_3d(srcfield)
        exactfield = initialize_field_grid_3d(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    regrid_method=esmpy.RegridMethod.BILINEAR,
                                    unmapped_action=esmpy.UnmappedAction.ERROR)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, exactfield, 
                                                   10E-02, 10E-02, 10E-16)

        self.assertAlmostEqual(meanrel, 0.00215601743167)
        self.assertAlmostEqual(csrvrel, 0.0)

    def test_grid_grid_3d_bilinear_spherical(self):
        # RO: This test creates the same Grid on every processor, it could be improved

        # create a grid
        srcgrid = grid_create_from_bounds_periodic_3d(60, 60, 14, corners=False)
        dstgrid = grid_create_from_bounds_periodic_3d(50, 50, 11, corners=False)

        # create Field objects on the Meshes
        srcfield = esmpy.Field(srcgrid, name='srcfield')
        dstfield = esmpy.Field(dstgrid, name='dstfield')
        exactfield = esmpy.Field(dstgrid, name='exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_grid_periodic_3d(srcfield)
        exactfield = initialize_field_grid_periodic_3d(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    regrid_method=esmpy.RegridMethod.BILINEAR,
                                    unmapped_action=esmpy.UnmappedAction.IGNORE)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, exactfield,
                                                   10E-03, 10E-03, 10E-16)

        self.assertAlmostEqual(meanrel, 0.00061587737764545617)
        self.assertAlmostEqual(csrvrel, 0.0)

    def test_grid_grid_regrid_csrv_mask_3D(self):
        # RO: This test creates the same Grid on every processor, it could be improved

        # create a grid
        srcgrid = grid_create_from_bounds_3d([0, 21], [0, 21], [0, 21], 21, 21, 21, corners=True)
        dstgrid = grid_create_from_bounds_3d([0.5, 19.5], [0.5, 19.5], [0.5, 19.5], 19, 19, 19, corners=True)

        # create Field objects on the Meshes
        srcfield = esmpy.Field(srcgrid, name='srcfield')
        srcfracfield = esmpy.Field(srcgrid, name='srcfracfield')
        dstfield = esmpy.Field(dstgrid, name='dstfield')
        dstfracfield = esmpy.Field(dstgrid, name='dstfracfield')
        exactfield = esmpy.Field(dstgrid, name='exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_grid_3d(srcfield)
        exactfield = initialize_field_grid_3d(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    regrid_method=esmpy.RegridMethod.CONSERVE,
                                    unmapped_action=esmpy.UnmappedAction.ERROR,
                                    src_frac_field=srcfracfield,
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_grid(srcfield,
                                    dofrac=True, fracfield=srcfracfield)
        dstmass = compute_mass_grid(dstfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, exactfield,
                                                   10E-02, 10E-02, 10E-16,
                                                   dstfracfield=dstfracfield,
                                                   mass1=srcmass, mass2=dstmass)

        self.assertAlmostEqual(meanrel, 0.0021560174316746865)
        self.assertAlmostEqual(csrvrel, 0.0)

    def test_grid_grid_regrid_csrv_mask(self):
        # RO: This test creates the same Grid on every processor, it could be improved

        # create two unique Grid objects
        srcgrid = grid_create_from_bounds([0, 21], [0, 21], 21, 21, corners=True, domask=True)
        dstgrid = grid_create_from_bounds([0.5, 19.5], [0.5, 19.5], 19, 19, corners=True)

        # create Field objects on the Meshes
        srcfield = esmpy.Field(srcgrid, name='srcfield')
        srcfracfield = esmpy.Field(srcgrid, name='srcfracfield')
        dstfield = esmpy.Field(dstgrid, name='dstfield')
        dstfracfield = esmpy.Field(dstgrid, name='dstfracfield')
        exactfield = esmpy.Field(dstgrid, name='exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_grid(srcfield)
        dstfield2 = initialize_field_grid(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    src_mask_values=np.atleast_1d(np.array([0])),
                                    regrid_method=esmpy.RegridMethod.CONSERVE,
                                    unmapped_action=esmpy.UnmappedAction.ERROR,
                                    src_frac_field=srcfracfield,
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_grid(srcfield,
                                    dofrac=True, fracfield=srcfracfield)
        dstmass = compute_mass_grid(dstfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, dstfield2, 
                                                   10E-2, 10E-2, 10E-16,
                                                   dstfracfield=dstfracfield,
                                                   mass1=srcmass, mass2=dstmass)

        self.assertAlmostEqual(meanrel, 0.0024803189848013785)
        self.assertAlmostEqual(csrvrel, 0.0)

    def test_grid_grid_regrid_csrv_2nd_mask(self):
        # RO: This test creates the same Grid on every processor, it could be improved

        # create two unique Grid objects
        srcgrid = grid_create_from_bounds([0, 21], [0, 21], 21, 21, corners=True, domask=True)
        dstgrid = grid_create_from_bounds([0.5, 19.5], [0.5, 19.5], 19, 19, corners=True)

        # create Field objects on the Meshes
        srcfield = esmpy.Field(srcgrid, name='srcfield')
        srcfracfield = esmpy.Field(srcgrid, name='srcfracfield')
        dstfield = esmpy.Field(dstgrid, name='dstfield')
        dstfracfield = esmpy.Field(dstgrid, name='dstfracfield')
        exactfield = esmpy.Field(dstgrid, name='exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_grid(srcfield)
        dstfield2 = initialize_field_grid(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    src_mask_values=np.atleast_1d(np.array([0])),
                                    regrid_method=esmpy.RegridMethod.CONSERVE_2ND,
                                    unmapped_action=esmpy.UnmappedAction.ERROR,
                                    src_frac_field=srcfracfield,
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_grid(srcfield,
                                    dofrac=True, fracfield=srcfracfield)
        dstmass = compute_mass_grid(dstfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, dstfield2, 
                                                   10E-2, 10E-2, 10E-16,
                                                   dstfracfield=dstfracfield,
                                                   mass1=srcmass, mass2=dstmass)

        self.assertAlmostEqual(meanrel, 0.0020296891000258252)
        self.assertAlmostEqual(csrvrel, 0.0)

    def test_grid_grid_regrid_srcmask_types(self):
        # NOTE: this tests an old issue where the items of a grid were not properly set when
        # the grid coord_typekind differed from the field typekind.

        # RO: This test creates the same Grid on every processor, it could be improved

        # create two unique Grid objects
        srcgrid = grid_create_from_bounds([0, 21], [0, 21], 21, 21, corners=True, domask=True,
                                          ctk=esmpy.TypeKind.R4)
        dstgrid = grid_create_from_bounds([0.5, 19.5], [0.5, 19.5], 19, 19, corners=True)

        # create Field objects on the Meshes
        srcfield = esmpy.Field(srcgrid, name='srcfield')
        srcfracfield = esmpy.Field(srcgrid, name='srcfracfield')
        dstfield = esmpy.Field(dstgrid, name='dstfield')
        dstfracfield = esmpy.Field(dstgrid, name='dstfracfield')
        exactfield = esmpy.Field(dstgrid, name='exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_grid(srcfield)
        dstfield2 = initialize_field_grid(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    src_mask_values=[0],
                                    regrid_method=esmpy.RegridMethod.CONSERVE,
                                    unmapped_action=esmpy.UnmappedAction.ERROR,
                                    src_frac_field=srcfracfield,
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_grid(srcfield,
                                    dofrac=True, fracfield=srcfracfield)
        dstmass = compute_mass_grid(dstfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, dstfield2, 
                                                   10E-2, 10E-2, 10E-16,
                                                   dstfracfield=dstfracfield,
                                                   mass1=srcmass, mass2=dstmass)

        self.assertAlmostEqual(meanrel, 0.0024803189848013785)
        self.assertAlmostEqual(csrvrel, 0.0)

    @pytest.mark.skipif(pet_count() not in {1, 4}, reason="test requires 1 or 4 cores")
    def test_grid_mesh_regrid_csrv_mask(self):
        mesh = None
        if pet_count() == 4:
            mesh, nodeCoord, nodeOwner, elemType, elemConn, elemMask, elemArea = \
                mesh_create_50_parallel(domask=True, doarea=True)
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn, elemMask, elemArea = \
                mesh_create_50(domask=True, doarea=True)

        # create a grid
        grid = grid_create_from_bounds([0, 4], [0, 4], 8, 8, corners=True, doarea=True)

        # create Field objects on the Meshes
        srcfield = esmpy.Field(mesh, name='srcfield', meshloc=esmpy.MeshLoc.ELEMENT)
        srcfracfield = esmpy.Field(mesh, name='srcfracfield', meshloc=esmpy.MeshLoc.ELEMENT)

        # make gridded fields
        exactfield = esmpy.Field(grid, name='exactfield')
        dstfield = esmpy.Field(grid, name='dstfield')
        dstfracfield = esmpy.Field(grid, name='dstfracfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_mesh(srcfield, nodeCoord, nodeOwner, elemType, elemConn,
                                         domask=True, elemMask=elemMask)
        exactfield = initialize_field_grid(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    src_mask_values=np.atleast_1d(np.array([0])),
                                    regrid_method=esmpy.RegridMethod.CONSERVE,
                                    unmapped_action=esmpy.UnmappedAction.ERROR,
                                    src_frac_field=srcfracfield,
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_mesh(srcfield, dofrac=True,
                                    fracfield=srcfracfield)
        dstmass = compute_mass_grid(dstfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, exactfield, 
                                                   80E-1, 80E-1, 10E-15, 
                                                   dstfracfield=dstfracfield,
                                                   mass1=srcmass, mass2=dstmass)

        self.assertAlmostEqual(meanrel, 0.038806630051265847)
        self.assertAlmostEqual(csrvrel, 0.0)

    @pytest.mark.skipif(pet_count() not in {1, 4}, reason="test requires 1 or 4 cores")
    def test_grid_mesh_regrid_csrv(self):
        mesh = None
        if pet_count() == 4:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn, _ = \
                mesh_create_50()

        # create a grid
        grid = grid_create_from_bounds([0, 4], [0, 4], 8, 8, corners=True)

        # create Fields
        srcfield = esmpy.Field(mesh, name='srcfield', meshloc=esmpy.MeshLoc.ELEMENT)
        srcfracfield = esmpy.Field(mesh, name='srcfracfield', meshloc=esmpy.MeshLoc.ELEMENT)
        dstfield = esmpy.Field(grid, name='dstfield')
        dstfracfield = esmpy.Field(grid, name='dstfracfield')
        exactfield = esmpy.Field(grid, name='exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_mesh(srcfield, nodeCoord, nodeOwner, elemType, elemConn)
        exactfield = initialize_field_grid(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    regrid_method=esmpy.RegridMethod.CONSERVE,
                                    norm_type=esmpy.NormType.FRACAREA,
                                    unmapped_action=esmpy.UnmappedAction.ERROR,
                                    src_frac_field=srcfracfield,
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_mesh(srcfield,
                                    dofrac=True, fracfield=srcfracfield)
        dstmass = compute_mass_grid(dstfield,
                                    dofrac=True, fracfield=dstfracfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, exactfield, 
                                                   50E-1, 50E-1, 10E-16, 
                                                   dstfracfield=dstfracfield,
                                                   mass1=srcmass, mass2=dstmass)

        self.assertAlmostEqual(meanrel, 0.037733241800767432)
        self.assertAlmostEqual(csrvrel, 0.0)

    @pytest.mark.skipif(pet_count() not in {1, 4}, reason="test requires 1 or 4 cores")
    def test_grid_mesh_regrid_mask(self):
       # create a grid
        grid = grid_create_from_bounds([0, 4], [0, 4], 8, 8, corners=True, domask=True)

        mesh = None
        if pet_count() == 4:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn, _ = \
                mesh_create_50()

        # create Field objects
        srcfield = esmpy.Field(mesh, name='srcfield')
        dstfield = esmpy.Field(grid, name='dstfield')
        exactfield = esmpy.Field(grid, name='exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_mesh(srcfield, nodeCoord, nodeOwner, elemType, elemConn)
        exactfield = initialize_field_grid(exactfield, domask=True)

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    dst_mask_values=np.atleast_1d(np.array([0])),
                                    regrid_method=esmpy.RegridMethod.BILINEAR,
                                    unmapped_action=esmpy.UnmappedAction.IGNORE)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, exactfield, 
                                                   20E-1, 20E-1, 10E-16, 
                                                   regrid_method=esmpy.RegridMethod.BILINEAR)

        self.assertAlmostEqual(meanrel, 0.0)
        self.assertAlmostEqual(csrvrel, 0.0)

    @pytest.mark.skipif(pet_count() not in {1, 4}, reason="test requires 1 or 4 cores")
    def test_grid_mesh_regrid(self):
       # create a grid
        grid = grid_create_from_bounds([0, 4], [0, 4], 8, 8, corners=True)

        mesh = None
        if pet_count() == 4:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn, _ = \
                mesh_create_50()

        # create Field objects
        srcfield = esmpy.Field(mesh, name='srcfield')
        dstfield = esmpy.Field(grid, name='dstfield')
        exactfield = esmpy.Field(grid, name='exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_mesh(srcfield, nodeCoord, nodeOwner, elemType, elemConn)
        exactfield = initialize_field_grid(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    regrid_method=esmpy.RegridMethod.BILINEAR,
                                    unmapped_action=esmpy.UnmappedAction.ERROR)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, exactfield, 
                                                   40E-2, 40E-2, 10E-16, 
                                                   regrid_method=esmpy.RegridMethod.BILINEAR)

        self.assertAlmostEqual(meanrel, 0.0)
        self.assertAlmostEqual(csrvrel, 0.0)

    @pytest.mark.skipif(pet_count() not in {1, 4}, reason="test requires 1 or 4 cores")
    def test_field_regrid_extrapolation(self):
        # create a grid
        grid = grid_create_from_bounds([0, 4], [0, 4], 8, 8, corners=True)

        mesh = None
        if pet_count() == 4:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn, _ = \
                mesh_create_50()

        # create Field objects
        srcfield = esmpy.Field(grid, name='srcfield')
        dstfield = esmpy.Field(mesh, name='dstfield')
        exactfield = esmpy.Field(mesh, name='exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_grid(srcfield)
        exactfield = initialize_field_mesh(exactfield, nodeCoord, nodeOwner, elemType, elemConn)

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    regrid_method=esmpy.RegridMethod.BILINEAR,
                                    extrap_method=esmpy.ExtrapMethod.NEAREST_IDAVG,
                                    extrap_num_src_pnts=10,
                                    extrap_dist_exponent=1.2,
                                    unmapped_action=esmpy.UnmappedAction.ERROR)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, exactfield, 
                                                   40E-2, 40E-2, 10E-16, 
                                                   regrid_method=esmpy.RegridMethod.BILINEAR)

        self.assertAlmostEqual(meanrel, 0.0)
        self.assertAlmostEqual(csrvrel, 0.0)

    @pytest.mark.skipif(pet_count() not in {1, 4}, reason="test requires 1 or 4 cores")
    def test_field_regrid_extrapolation_creepfill(self):
        # create a grid
        grid = grid_create_from_bounds([0, 4], [0, 4], 8, 8, corners=True)

        mesh = None
        if pet_count == 4:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn, _ = \
                mesh_create_50()

        # create Field objects
        srcfield = esmpy.Field(mesh, name='dstfield')
        dstfield = esmpy.Field(grid, name='srcfield')
        exactfield = esmpy.Field(grid, name='exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_mesh(srcfield, nodeCoord, nodeOwner, elemType, elemConn)
        exactfield = initialize_field_grid(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    regrid_method=esmpy.RegridMethod.BILINEAR,
                                    extrap_method=esmpy.ExtrapMethod.CREEP_FILL,
                                    extrap_num_levels=100)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, exactfield, 
                                                   40E-2, 40E-2, 10E-16, 
                                                   regrid_method=esmpy.RegridMethod.BILINEAR)

        self.assertAlmostEqual(meanrel, 0.0)
        self.assertAlmostEqual(csrvrel, 0.0)

    @pytest.mark.skipif(pet_count() not in {1, 4}, reason="test requires 1 or 4 cores")
    def test_mesh_mesh_regrid(self):
        srcmesh = None
        dstmesh = None
        if pet_count() == 4:
            srcmesh, nodeCoordSrc, nodeOwnerSrc, elemTypeSrc, elemConnSrc = \
                mesh_create_50_parallel()
            dstmesh, nodeCoordDst, nodeOwnerDst, elemTypeDst, elemConnDst = \
                mesh_create_10_parallel()
        else:
            srcmesh, nodeCoordSrc, nodeOwnerSrc, elemTypeSrc, elemConnSrc, _ = \
                mesh_create_50()
            dstmesh, nodeCoordDst, nodeOwnerDst, elemTypeDst, elemConnDst, _ = \
                mesh_create_10()

        # create ESMP_Field objects on the Meshes
        srcfield = esmpy.Field(srcmesh, name='srcfield', meshloc=esmpy.MeshLoc.ELEMENT)
        srcfracfield = esmpy.Field(srcmesh, name='srcfracfield', meshloc=esmpy.MeshLoc.ELEMENT)
        dstfield = esmpy.Field(dstmesh, name='dstfield', meshloc=esmpy.MeshLoc.ELEMENT)
        dstfracfield = esmpy.Field(dstmesh, name='dstfracfield', meshloc=esmpy.MeshLoc.ELEMENT)
        exactfield = esmpy.Field(dstmesh, name='exactfield', meshloc=esmpy.MeshLoc.ELEMENT)

        # initialize the Fields to an analytic function
        srcfield = initialize_field_mesh(srcfield, nodeCoordSrc, nodeOwnerSrc,
                                         elemTypeSrc, elemConnSrc)
        exactfield = initialize_field_mesh(exactfield, nodeCoordDst, nodeOwnerDst,
                                           elemTypeDst, elemConnDst)

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    regrid_method=esmpy.RegridMethod.CONSERVE,
                                    norm_type=esmpy.NormType.FRACAREA,
                                    unmapped_action=esmpy.UnmappedAction.ERROR,
                                    ignore_degenerate=True,
                                    src_frac_field=srcfracfield,
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_mesh(srcfield,
                                    dofrac=True, fracfield=srcfracfield)
        dstmass = compute_mass_mesh(dstfield,
                                    dofrac=True, fracfield=dstfracfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, exactfield, 
                                                   20E-2, 20E-2, 10E-16, 
                                                   dstfracfield=dstfracfield,
                                                   mass1=srcmass, mass2=dstmass)

        self.assertAlmostEqual(meanrel, 0.037109375)
        self.assertAlmostEqual(csrvrel, 0.0)

    @pytest.mark.skipif(pet_count() not in {1, 4}, reason="test requires 1 or 4 cores")
    def est_grid_mesh_pentatri_regrid_csrv(self):
        mesh = None
        if pet_count() == 4:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_ngons_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_ngons()

        # create a grid
        grid = grid_create_from_bounds([0, 4], [0, 4], 8, 8, corners=True, doarea=True)

        # create Field objects on the Meshes
        srcfield = esmpy.Field(mesh, name='srcfield', meshloc=esmpy.MeshLoc.ELEMENT)
        srcfracfield = esmpy.Field(mesh, name='srcfracfield', meshloc=esmpy.MeshLoc.ELEMENT)

        # make gridded fields
        exactfield = esmpy.Field(grid, name='exactfield')
        dstfield = esmpy.Field(grid, name='dstfield')
        dstfracfield = esmpy.Field(grid, name='dstfracfield')

        # initialize the Fields to an analytic function
        # srcfield = initialize_field_mesh(srcfield, nodeCoord, nodeOwner, elemType, elemConn)
        # exactfield = initialize_field_grid(exactfield)
        # TODO: cannot make analytic fields on ngons yet
        srcfield.data[...] = 25.
        exactfield.data[...] = 25.

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    regrid_method=esmpy.RegridMethod.CONSERVE,
                                    unmapped_action=esmpy.UnmappedAction.ERROR,
                                    src_frac_field=srcfracfield,
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_mesh(srcfield, dofrac=True,
                                    fracfield=srcfracfield)
        dstmass = compute_mass_grid(dstfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, exactfield, 
                                                   80E-1, 80E-1, 10E-15, 
                                                   dstfracfield=dstfracfield,
                                                   mass1=srcmass, mass2=dstmass)

        assert (meanrel < 10E-2)
        assert (csrvrel < 10E-14)

    @pytest.mark.skipif(pet_count()!=1, reason="test must be run in serial")
    def est_grid_mesh_pentatri_regrid_csrv_simple(self):
        # create a Mesh
        mesh, nodeCoord, nodeOwner, elemType, elemConn = \
            mesh_create_4_ngons()

        # create a grid
        grid = grid_create_from_bounds([0, 4], [0, 4], 8, 8, corners=True, doarea=True)

        # create Field objects on the Meshes
        srcfield = esmpy.Field(mesh, name='srcfield', meshloc=esmpy.MeshLoc.ELEMENT)
        srcfracfield = esmpy.Field(mesh, name='srcfracfield', meshloc=esmpy.MeshLoc.ELEMENT)

        # make gridded fields
        exactfield = esmpy.Field(grid, name='exactfield')
        dstfield = esmpy.Field(grid, name='dstfield')
        dstfracfield = esmpy.Field(grid, name='dstfracfield')

        # initialize the Fields to an analytic function
        # srcfield = initialize_field_mesh(srcfield, nodeCoord, nodeOwner, elemType, elemConn)
        # exactfield = initialize_field_grid(exactfield)
        # TODO: cannot make analytic fields on ngons yet
        srcfield.data[...] = 25.
        exactfield.data[...] = 25.

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    regrid_method=esmpy.RegridMethod.CONSERVE,
                                    unmapped_action=esmpy.UnmappedAction.ERROR,
                                    src_frac_field=srcfracfield,
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_mesh(srcfield, dofrac=True,
                                    fracfield=srcfracfield)
        dstmass = compute_mass_grid(dstfield)

        # compare results and output PASS or FAIL
        meanrel, csrvrel, correct = compare_fields(dstfield, exactfield, 
                                                   80E-1, 80E-1, 10E-15,
                                                   dstfracfield=dstfracfield, 
                                                   mass1=srcmass, mass2=dstmass)

        assert (meanrel < 10E-2)
        assert (csrvrel < 10E-14)

    @pytest.mark.skipif(pet_count() not in {1, 4}, reason="test requires 1 or 4 cores")
    def test_grid_mesh_pentatri_regrid_bilinear(self):
        mesh = None
        if pet_count() == 4:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_ngons_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_ngons()

        # create a grid
        grid = grid_create_from_bounds([0, 4], [0, 4], 8, 8, corners=True, doarea=True)

        # create Field objects on the Meshes
        srcfield = esmpy.Field(mesh, name='srcfield', meshloc=esmpy.MeshLoc.NODE)

        # make gridded fields
        exactfield = esmpy.Field(grid, name='exactfield')
        dstfield = esmpy.Field(grid, name='dstfield')

        # initialize the Fields to an analytic function
        # srcfield = initialize_field_mesh(srcfield, nodeCoord, nodeOwner, elemType, elemConn)
        # exactfield = initialize_field_grid(exactfield)
        # TODO: cannot make analytic fields on ngons yet
        srcfield.data[...] = 25.
        exactfield.data[...] = 25.

        # run the ESMF regridding
        regridSrc2Dst = esmpy.Regrid(srcfield, dstfield,
                                    regrid_method=esmpy.RegridMethod.BILINEAR,
                                    unmapped_action=esmpy.UnmappedAction.ERROR)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compare results and output PASS or FAIL
        meanrel, _, _ = compare_fields(dstfield, exactfield, 80E-1, 80E-1, 10E-16)

        self.assertAlmostEqual(meanrel, 0)
