import os, sys
import numpy                        as np
import pandas                       as pd
import nk_toolkit.plot.load__config as lcf
import nk_toolkit.plot.gplot1D      as gp1

# ========================================================= #
# ===  plot__refparticle.py                             === #
# ========================================================= #
def plot__refparticle( inpFile=None ):

    ylabels  = { "beta"       : r"$\beta$"        ,
                 "gamma"      : r"$\gamma$"       ,
                 "beta_gamma" : r"$\beta \gamma$" ,
                 "x"          : r"$x$ [m]"        ,
                 "y"          : r"$y$ [m]"        ,
                 "z"          : r"$z$ [m]"        ,
                 "t"          : r"$ct$ [m]"       ,
                 "px"         : r"$p_x$ [rad]"    ,
                 "py"         : r"$p_y$ [rad]"    ,
                 "pz"         : r"$p_z$ [rad]"    ,
                 "pt"         : r"$p_t$ [rad]"    ,
                }
    THRESHOLD = 1e32
    
    # ------------------------------------------------- #
    # --- [1] load .stat file                       --- #
    # ------------------------------------------------- #
    data    = pd.read_csv( inpFile, sep=r"\s+" )
    data    = data.where( data.abs() <= THRESHOLD, np.nan )
    xAxis   = data["s"]
    
    # ------------------------------------------------- #
    # --- [2] plot config                           --- #
    # ------------------------------------------------- #
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [10.5,3.5],
        "figure.position"    : [ 0.10, 0.15, 0.97, 0.93 ],
        "ax1.x.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.y.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.x.label"        : "s [m]",
        "ax1.x.minor.nticks" : 1, 
        "plot.marker"        : "o",
        "plot.markersize"    : 2.0,
        "legend.fontsize"    : 8.0, 
    }
    config = { **config, **config_ }

    # ------------------------------------------------- #
    # --- [3] xyt range ( mean, min, max ) graph    --- #
    # ------------------------------------------------- #
    for key,hylabel in ylabels.items():
        config_  = {
            "figure.pngFile"     : "png/refp__s-{0}.png".format( key ), 
            "ax1.y.label"        : hylabel,
        }
        config = { **config, **config_ }
        fig    = gp1.gplot1D( config=config )
        fig.add__plot( xAxis=xAxis, yAxis=data[key] )
        fig.set__axis()
        fig.save__figure()


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    inpFile = "impactx/diags/ref_particle.0.0"
    plot__refparticle( inpFile=inpFile )
