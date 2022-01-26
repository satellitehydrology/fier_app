import numpy as np
import ee
import xarray as xr
import restee as ree
import numpy as np
import matplotlib.pyplot as plt
import dask
import fierpy
from eofs.xarray import Eof


# ----- Rotated EOF -----
def reof(stack: xr.DataArray, variance_threshold: float = 0.8, n_modes: int = 4) -> xr.Dataset:
    """Function to perform rotated empirical othogonal function (eof) on a spatial timeseries

    Update: Sort rotated modes of spatiotemporal pattern

    args:
        stack (xr.DataArray): DataArray of spatial temporal values with coord order of (t,y,x)
        variance_threshold(float, optional): optional fall back value to select number of eof
            modes to use. Only used if n_modes is less than 1. default = 0.727
        n_modes (int, optional): number of eof modes to use. default = 4

    returns:
        xr.Dataset: rotated eof dataset with spatial modes, temporal modes, and mean values
            as variables

    """
    # extract out some dimension shape information
    shape3d = stack.shape
    spatial_shape = shape3d[1:]
    shape2d = (shape3d[0],np.prod(spatial_shape))

    # flatten the data from [t,y,x] to [t,...]
    da_flat = xr.DataArray(
        stack.values.reshape(shape2d),
        coords = [stack.time,np.arange(shape2d[1])],
        dims=['time','space']
    )
    #logger.debug(da_flat)

    ## find the temporal mean for each pixel
    center = da_flat.mean(dim='time')

    centered = da_flat - center

    # get an eof solver object
    solver = Eof(centered,center=False)

    # check if the n_modes keyword is set to a realistic value
    # if not get n_modes based on variance explained
    if n_modes < 0:
        #n_modes = int((solver.varianceFraction().cumsum() < variance_threshold).sum())
        n_modes = int(np.argwhere(solver.varianceFraction().cumsum().values >= variance_threshold)[0]+1)
    # calculate to spatial eof values
    eof_components = solver.eofs(neofs=n_modes).transpose()

    # get cumulative variance fractions of eof (up to the max. retained mode)
    total_eof_var_frac = solver.varianceFraction(neigs=n_modes).cumsum().values[-1]

    # get the indices where the eof is valid data
    non_masked_idx = np.where(np.logical_not(np.isnan(eof_components[:,0])))[0]

    # create a "blank" array to set rotated values to
    rotated = eof_components.values.copy()

    # # waiting for release of sklean version >= 0.24
    # # until then have a placeholder function to do the rotation
    # fa = FactorAnalysis(n_components=n_modes, rotation="varimax")
    # rotated[non_masked_idx,:] = fa.fit_transform(eof_components[non_masked_idx,:])

    # apply varimax rotation to eof components
    # placeholder function until sklearn version >= 0.24
    rotated[non_masked_idx,:] = _ortho_rotation(eof_components[non_masked_idx,:])

    # project the original time series data on the rotated eofs
    projected_pcs = np.dot(centered[:,non_masked_idx], rotated[non_masked_idx,:])

    # get variance of each rotated mode
    rot_var = np.var(projected_pcs, axis=0)
    # get cumulative variance of all rotated modes
    total_rot_var = rot_var.cumsum()[-1]
    # get variance fraction of each rotated mode

    # Rotation re-distributes the variance of each mode. So we have to calculate
    # the explained variance of each mode and sort them
    rot_var_frac = ((rot_var/total_rot_var)*total_eof_var_frac)*100

    # reshape the rotated eofs to a 3d array of [y,x,c]
    spatial_rotated = rotated.reshape(spatial_shape+(n_modes,))


    # sort modes based on variance fraction of REOF
    indx_rot_var_frac_sort = np.expand_dims(((np.argsort(-1*rot_var_frac)).data), axis=0)
    projected_pcs = np.take_along_axis(projected_pcs,indx_rot_var_frac_sort,axis=1)

    indx_rot_var_frac_sort = np.expand_dims(indx_rot_var_frac_sort, axis=0)
    spatial_rotated = np.take_along_axis(spatial_rotated,indx_rot_var_frac_sort,axis=2)

    # structure the spatial and temporal reof components in a Dataset
    reof_ds = xr.Dataset(
        {
            "spatial_modes": (["lat","lon","mode"],spatial_rotated),
            "temporal_modes":(["time","mode"],projected_pcs),
            "center": (["lat","lon"],center.values.reshape(spatial_shape))
        },
        coords = {
            "lon":(["lon"],stack.lon.data),
            "lat":(["lat"],stack.lat.data),
            "time":stack.time.data,
            "mode": np.arange(n_modes)+1
        }
    )

    return reof_ds, rot_var_frac[indx_rot_var_frac_sort]


def _ortho_rotation(components: np.array, method: str = 'varimax', tol: float = 1e-6, max_iter: int = 1000) -> np.array:
    """Return rotated components. Temp function"""
    nrow, ncol = components.shape
    rotation_matrix = np.eye(ncol)
    var = 0

    for _ in range(max_iter):
        comp_rot = np.dot(components, rotation_matrix)
        if method == "varimax":
            tmp = comp_rot * np.transpose((comp_rot ** 2).sum(axis=0) / nrow)
        elif method == "quartimax":
            tmp = 0
        u, s, v = np.linalg.svd(
            np.dot(components.T, comp_rot ** 3 - tmp))
        rotation_matrix = np.dot(u, v)
        var_new = np.sum(s)
        if var != 0 and var_new < var * (1 + tol):
            break
        var = var_new

    return np.dot(components, rotation_matrix)
