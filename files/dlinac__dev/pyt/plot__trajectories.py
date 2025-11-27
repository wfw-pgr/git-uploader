import os, sys, tqdm
import scipy  as sp
import numpy  as np
import pandas as pd
import matplotlib.pyplot            as plt
import nk_toolkit.plot.load__config as lcf
import nk_toolkit.plot.gplot1D      as gp1
import load__impactHDF5 as lih

# ========================================================= #
# ===  plot__trajectories.py                            === #
# ========================================================= #

def plot__trajectories( hdf5File=None, refpFile=None, obj="xp", pids=None, nColors=128 ):

    ylabels  = { "xp":"x [mm]", "yp":"y [mm]", "zp":"z [mm]" }
    
    # ------------------------------------------------- #
    # --- [1] load HDF5 file                        --- #
    # ------------------------------------------------- #
    pinfo    = lih.load__impactHDF5( inpFile=hdf5File )
    rinfo    = pd.read_csv( refpFile, sep=r"\s+"  )
    ref_s    = rinfo["s"]
    colors   = plt.get_cmap( "plasma", nColors )
    if ( pids is None ):
        pids = np.array( list( set( pinfo["pid"] ) ) )
    
    # ------------------------------------------------- #
    # --- [2] configuration                         --- #
    # ------------------------------------------------- #
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [10.5,3.5],
        "figure.position"    : [ 0.10, 0.12, 0.97, 0.95 ],
        "figure.pngFile"     : "png/trajectories.png", 
        "ax1.x.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.y.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.x.label"        : "s [m]",
        "ax1.y.label"        : ylabels[obj],
        "plot.marker"        : "none",
        "plot.linestyle"     : "-", 
        "plot.markersize"    : 0.2,
    }
    config = { **config, **config_ }

    # ------------------------------------------------- #
    # --- [3] plot                                  --- #
    # ------------------------------------------------- #
    fig    = gp1.gplot1D( config=config )
    for ik,pid in enumerate(tqdm.tqdm(pids)):
        trajectory = ( pinfo[ pinfo["pid"] == pid ] )[obj].values
        if ( len(trajectory) == 0 ): continue
        xAxis  = ref_s[:(len(trajectory))]
        hcolor = colors( ik%nColors )
        fig.add__plot( xAxis=xAxis, yAxis=trajectory, color=hcolor )
    fig.set__axis()
    fig.save__figure()
    return()


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    npart    = int(1e3)
    nplot    = int(1e3)
    obj      = "xp"
    hdf5File = "impactx/diags/openPMD/bpm.h5"
    refpFile = "impactx/diags/ref_particle.0.0"
    pids     = np.random.choice( np.arange(1,npart+1), size=nplot, replace=False )
    plot__trajectories( hdf5File=hdf5File, refpFile=refpFile, pids=pids, obj=obj )
