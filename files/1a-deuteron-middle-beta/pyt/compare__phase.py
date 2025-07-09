import numpy as np
import pandas as pd
import nkUtilities.load__config   as lcf
import nkUtilities.gplot1D        as gp1

# ========================================================= #
# ===  compare.py                                       === #
# ========================================================= #

def compare():

    hdirs    = [ "ph0deg/", "ph10deg/", "ph20deg/", "ph30deg/", "ph45deg/" ]
    
    # ------------------------------------------------- #
    # --- [3] plot data                             --- #
    # ------------------------------------------------- #
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [4.5,4.5],
        "figure.pngFile"     : "png/phasescan_tw_mad.png", 
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


    for hdir in hdirs:
        inpFile1 = hdir + "beam.out"
        inpFile2 = hdir + "ptc_twiss.h5"
        inpFile3 = hdir + "twiss__fromTrackLine.h5"
        
        cm, mrad = 1.0e-2, 1.0e-3
    
        # ------------------------------------------------- #
        # --- [1] load data                             --- #
        # ------------------------------------------------- #
        Data1  = pd.read_csv( inpFile1, sep=r"\s+", header=0 )
        Data2  = pd.read_hdf( inpFile2 )
        Data3  = pd.read_hdf( inpFile3 )
        s_bl1  = Data1["dist[m]"]
        betax1 = Data1["b_x[cm/mrad]"] * cm / mrad
        s_bl2  = Data2["S"]
        betax2 = Data2["BETX"]
        s_bl3  = Data3["S"]
        betax3 = Data3["beta_x"]

        # fig.add__plot( xAxis=s_bl1, yAxis=betax1, label=hdir+" Track-v38"    )
        fig.add__plot( xAxis=s_bl2, yAxis=betax2, label=hdir+"PTC-Twiss"     )
        fig.add__plot( xAxis=s_bl3, yAxis=betax3, label=hdir+"PTC-TrackLine" )
        
    fig.set__axis()
    fig.set__legend()
    fig.save__figure()
    
    return()


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    compare()

