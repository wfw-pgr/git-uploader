import os, sys
import pandas as pd
import numpy  as np
import nk_toolkit.plot.load__config   as lcf
import nk_toolkit.plot.gplot1D        as gp1

# ========================================================= #
# ===  plot__collectiveEnergy.py                        === #
# ========================================================= #

def plot__collectiveEnergy( paramsFile="dat/parameters.json", steps=None, pids=None ):

    mm, mrad  = 1.0e-3, 1.0e-3
    ns        = 1.0e-9
    cv        = 2.99792458e8
    Ek0       = 40.0
    
    # ------------------------------------------------- #
    # --- [1] get particle info                     --- #
    # ------------------------------------------------- #
    import nk_toolkit.impactx.impactx_toolkit as itk
    ptcls        = itk.get__particles( paramsFile=paramsFile, steps=steps, pids=pids )
    ptcls["Ek"]  = ptcls["Ek"]
    ptcls["dt"]  = ptcls["dt"]  / ns
    if ( ( isinstance( steps, (int,float) ) ) or ( steps is None ) ):
        steps = sorted( list( set( ptcls["step"] ) ) )
    
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [4.5,4.5],
        "figure.pngFile"     : "png/collectiveEnergy.png", 
        "figure.position"    : [ 0.16, 0.16, 0.94, 0.94 ],
        "ax1.y.normalize"    : 1.0e0, 
        "ax1.x.range"        : { "auto":False, "min":  0.0, "max": 80.0, "num": 9 },
        "ax1.y.range"        : { "auto":False, "min":  0.0, "max":200.0, "num":11 },
        "ax1.x.label"        : "s [m]",
        "ax1.y.label"        : "Energy [MeV]",
        "ax1.x.minor.nticks" : 1, 
        "plot.marker"        : "none",
        "plot.markersize"    : 3.0,
        "legend.fontsize"    : 9.0, 
    }
    config = { **config, **config_ }

    stack = []
    for ik,step in enumerate(steps):
        eAxis         = np.linspace( 0.0, 200.0, 201 )
        energy_       = ptcls[ ptcls["step"] == step ]
        energy        = energy_["Ek"]
        ref_s         = energy_["ref_s"].iloc[0]
        minE, maxE    = np.min ( energy ), np.max   ( energy )
        meanE, mediE  = np.mean( energy ), np.median( energy )
        stack        += [ [ step, ref_s, minE, maxE, meanE, mediE ] ]

    data   = np.array( stack )
    fig    = gp1.gplot1D( config=config )
    fig.add__plot( xAxis=data[:,1], yAxis=data[:,2], label="min(E)" )
    fig.add__plot( xAxis=data[:,1], yAxis=data[:,3], label="max(E)" )
    fig.add__plot( xAxis=data[:,1], yAxis=data[:,4], label="mean(E)" )
    fig.add__plot( xAxis=data[:,1], yAxis=data[:,5], label="median(E)" )
    fig.set__axis()
    fig.set__legend()
    fig.save__figure()
    return()



# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    plot__collectiveEnergy( steps=None )

