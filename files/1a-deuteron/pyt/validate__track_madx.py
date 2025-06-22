import numpy  as np
import pandas as pd

# ========================================================= #
# ===  validate__track_madx.py                          === #
# ========================================================= #

def validate__track_madx():

    cm   = 1.0e-2
    mrad = 1.0e-3
    
    # ------------------------------------------------- #
    # --- [1] load track data                       --- #
    # ------------------------------------------------- #
    trackFile = "track/beam.out"
    track     = pd.read_csv( trackFile, sep=r"\s+", header=0 )
    track_x   = track["dist[m]"]
    track_y   = track["b_x[cm/mrad]"] * cm / mrad

    # ------------------------------------------------- #
    # --- [2] load madx twiss data                  --- #
    # ------------------------------------------------- #
    twissFile = "madx/out/twiss.csv"
    twiss     = pd.read_csv( twissFile, header=0 )
    twiss_x   = twiss["S"]
    twiss_y   = twiss["BETX"]
    
    # ------------------------------------------------- #
    # --- [3] plot compare                          --- #
    # ------------------------------------------------- #
    import nkUtilities.load__config   as lcf
    import nkUtilities.gplot1D        as gp1
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [8,3],
        "figure.pngFile"     : "png/validate__track_madx.png", 
        "figure.position"    : [ 0.16, 0.16, 0.94, 0.94 ],
        "ax1.y.normalize"    : 1.0e0, 
        "ax1.x.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.y.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.x.label"        :  "s (m)",
        "ax1.y.label"        : r"$\beta_x \mathrm{(m)}$",
        "ax1.x.minor.nticks" : 1, 
        "plot.marker"        : "o",
        "plot.markersize"    : 3.0,
        "legend.fontsize"    : 9.0, 
    }
    config = { **config, **config_ }
    
    fig    = gp1.gplot1D( config=config )
    fig.add__plot( xAxis=track_x, yAxis=track_y, label="track" )
    fig.add__plot( xAxis=twiss_x, yAxis=twiss_y, label="mad-x" )
    fig.set__axis()
    fig.set__legend()
    fig.save__figure()

    print( twiss_y / track_y )

    
    return()


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    validate__track_madx()
    
