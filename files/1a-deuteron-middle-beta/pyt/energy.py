import os, sys
import pandas as pd
import nk_toolkit.plot.load__config  as lcf
import nk_toolkit.plot.gplot1D       as gp1

# ========================================================= #
# ===  calculate__energy.py                             === #
# ========================================================= #
def calculate__energy( inpFile="madx/out/track.tfsone", outFile="dat/energy.csv" ):

    hdfFile  = "madx/out/trackline.h5"
    track    = pd.read_hdf( hdfFile )
    
    s        = track["S"]
    Etot     = track["E"]
    umass    = 0.931494                 # [GeV]
    MeV_u    = 1000.0 /2.0
    E0_d     = 2.014 * umass
    Ek       = ( Etot - E0_d ) * MeV_u  # [MeV/u]
    
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [4.5,4.5],
        "figure.pngFile"     : "png/Ek.png", 
        "figure.position"    : [ 0.18, 0.18, 0.94, 0.94 ],
        "ax1.y.normalize"    : 1.0e0, 
        "ax1.x.range"        : { "auto":True, "min": 0.0, "max":80.0, "num":9 },
        "ax1.y.range"        : { "auto":True, "min": 0.0, "max":100.0, "num":11 },
        "ax1.x.label"        : r"$s$  (m)",
        "ax1.y.label"        : r"$E_k$ (MeV/u)",
        "ax1.x.minor.nticks" : 1, 
        "plot.marker"        : "o",
        "plot.markersize"    : 3.0,
        "legend.fontsize"    : 9.0, 
    }
    config = { **config, **config_ }
    
    fig    = gp1.gplot1D( config=config )
    fig.add__plot( xAxis=s, yAxis=Ek, label="kinetic [MeV/u]" )
    fig.set__axis()
    fig.set__legend()
    fig.save__figure()

# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    calculate__energy()
