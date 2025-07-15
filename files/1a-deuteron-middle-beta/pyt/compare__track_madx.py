import os, sys, json5
import numpy  as np
import pandas as pd
import nkUtilities.load__config as lcf
import nkUtilities.gplot1D      as gp1

# ========================================================= #
# ===  compare__track_madx.py                           === #
# ========================================================= #

def compare__track_madx( paramsFile="dat/parameters.json" ):


    cm, mrad   = 1.0e-2, 1.0e-3
    
    # ------------------------------------------------- #
    # --- [1] load data                             --- #
    # ------------------------------------------------- #
    with open( paramsFile, "r" ) as f:
        params = json5.load( f )
    track_track = pd.read_csv( params["post.compare.trackFile"], sep=r"\s+", header=0 )
    madx_twiss  = pd.read_csv( params["post.twiss.outFile"], header=0 )
    madx_track  = pd.read_csv( params["post.track.outFile"], header=0 )
    sL1         = track_track["dist[m]"]
    bx1         = track_track["b_x[cm/mrad]"] * cm / mrad
    sL2         =  madx_twiss["S"]
    bx2         =  madx_twiss["BETX"]
    sL3         =  madx_track["S"]
    bx3         =  madx_track["beta_x"]

    # ------------------------------------------------- #
    # --- [3] plot data                             --- #
    # ------------------------------------------------- #
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [4.5,4.5],
        "figure.pngFile"     : params["post.compare.pngFile"], 
        "figure.position"    : [ 0.16, 0.16, 0.94, 0.94 ],
        "ax1.y.normalize"    : 1.0e0, 
        "ax1.x.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.y.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.x.label"        : "s [m]",
        "ax1.y.label"        : r"$\beta_x$ [m]",
        "ax1.x.minor.nticks" : 1, 
        "plot.marker"        : "o",
        "plot.markersize"    : 3.0,
        "legend.fontsize"    : 9.0, 
    }
    config = { **config, **config_ }
    
    fig    = gp1.gplot1D( config=config )
    fig.add__plot( xAxis=sL1, yAxis=bx1, label="Track-v38"  )
    fig.add__plot( xAxis=sL2, yAxis=bx2, label="MADX-Twiss" )
    fig.add__plot( xAxis=sL3, yAxis=bx3, label="MADX-Track" )
    fig.set__axis()
    fig.set__legend()
    fig.save__figure()
    return()



# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    compare__track_madx()
    
