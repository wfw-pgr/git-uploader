import os, sys
import numpy                        as np
import pandas                       as pd
import nk_toolkit.plot.load__config as lcf
import nk_toolkit.plot.gplot1D      as gp1
import nk_toolkit.impactx.impactx_toolkit as itk


# ========================================================= #
# ===  plot__statistics.py                              === #
# ========================================================= #
def plot__statistics( inpFile=None, pngDir="png/", plot_conf=None  ):

    lattice  = True
    ylabels_ = { "x-range"        : "x [m]"                 ,
                 "y-range"        : "y [m]"                 ,
                 "t-range"        : "t [m]"                 ,
                 "px-range"       : "px"                    ,
                 "py-range"       : "py"                    ,
                 "pt-range"       : "pt"                    ,
                 "sig_xyt"        : "RMS beam size [m]"     , 
                 "sig_pxyt"       : "Momentum"              ,
                 "alpha_xyt"      : r"$\alpha$"             ,
                 "beta_xyt"       : r"$\beta$ [m]"          ,
                 "dispersion_xy"  : r"$D_x, D_y$ [m]"     ,
                 "dispersion_pxy" : r"$D_x^\prime, D_y^\prime$ [a.u.]",
                 "emittance_xyt"  : r"$\epsilon$ [m rad]"   ,
                 "emittance_xytn" : r"$\epsilon_n$ [m  rad]",
                 "charge_C"       : "Charge [C]"            , 
                }
    THRESHOLD = 1.e30
    
    # ------------------------------------------------- #
    # --- [1] load .stat file                       --- #
    # ------------------------------------------------- #
    data    = pd.read_csv( inpFile, sep=r"\s+" )
    data    = data.where( data.abs() <= THRESHOLD, np.nan )
    ylabels = { key:key for key in data.keys() }
    ylabels = { **ylabels, **ylabels_ }

    nparticle_threshold = 0.10
    if ( nparticle_threshold ):
        fraction = ( data["charge_C"] ) / ( data["charge_C"][0] )
        data     = data.where( fraction >= nparticle_threshold, np.nan )
    
    # ------------------------------------------------- #
    # --- [2] plot config                           --- #
    # ------------------------------------------------- #
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [10.5,3.5],
        "figure.position"    : [ 0.10, 0.15, 0.97, 0.93 ],
        "ax1.x.range"        : { "auto":False, "min": 0.0, "max":80.0, "num":9 },
        "ax1.y.range"        : { "auto":True , "min": 0.0, "max":1.0, "num":11 },
        "ax1.x.label"        : "s [m]",
        "ax1.x.minor.nticks" : 1, 
        "plot.marker"        : "o",
        "plot.markersize"    : 2.0,
        "legend.fontsize"    : 8.0, 
    }
    config = { **config, **config_ }
    if ( plot_conf is not None ):
        config = { **config, **plot_conf }        


    # ------------------------------------------------- #
    # --- [3] xyt range ( mean, min, max ) graph    --- #
    # ------------------------------------------------- #
    for xyt in ["x","y","t", "px","py","pt"]:
        config_  = {
            "figure.pngFile" : os.path.join( pngDir, "stat__s-{0}-range.png".format( xyt ) ), 
            "ax1.y.label"    : ylabels["{}-range".format( xyt )],
        }
        config = { **config, **config_ }
        fig    = gp1.gplot1D( config=config )
        fig.add__plot( xAxis=data["s"], yAxis=data[xyt+"_mean"], label="Mean" )
        fig.add__plot( xAxis=data["s"], yAxis=data[xyt+"_min"] , label="Min"  )
        fig.add__plot( xAxis=data["s"], yAxis=data[xyt+"_max"] , label="Max"  )
        fig.set__axis()
        fig.set__legend()
        fig.save__figure()

    # ------------------------------------------------- #
    # --- [4] statistics graph                      --- #
    # ------------------------------------------------- #
    for stat in [ "sig_{}", "sig_p{}", "alpha_{}", "beta_{}", \
                  "emittance_{}", "emittance_{}n" ]:
        gname    = stat.format( "xyt" )
        config_  = {
            "figure.pngFile" : os.path.join( pngDir, "stat__s-{0}.png".format( gname ) ), 
            "ax1.y.label"    : ylabels[gname],
        }
        config = { **config, **config_ }
        fig    = gp1.gplot1D( config=config )
        fig.add__plot( xAxis=data["s"], yAxis=data[stat.format("x")], label=stat.format("x") )
        fig.add__plot( xAxis=data["s"], yAxis=data[stat.format("y")], label=stat.format("y")  )
        fig.add__plot( xAxis=data["s"], yAxis=data[stat.format("t")], label=stat.format("t")  )
        fig.set__axis()
        fig.set__legend()
        fig.save__figure()

    # ------------------------------------------------- #
    # --- [5] dispersion                            --- #
    # ------------------------------------------------- #
    for stat in [ "dispersion_{}", "dispersion_p{}", ]:
        gname    = stat.format( "xy" )
        config_  = {
            "figure.pngFile" : os.path.join( pngDir, "s-{0}.png".format( gname ) ), 
            "ax1.y.label"    : ylabels[gname],
            "ax1.x.range"    : { "auto":False, "min":  0.0, "max":7.0, "num":8  },
            "ax1.y.range"    : { "auto":False, "min": -5.0, "max":5.0, "num":11 },
        }
        config = { **config, **config_ }
        fig    = gp1.gplot1D( config=config )
        fig.add__plot( xAxis=data["s"], yAxis=data[stat.format("x")], label=stat.format("x") )
        fig.add__plot( xAxis=data["s"], yAxis=data[stat.format("y")], label=stat.format("y")  )
        if ( lattice ):
            itk.plot__lattice( latticeFile="dat/beamline_impactx.json", ax=fig.ax1, \
                               height=1.0, y0=-3.0 )
        fig.set__axis()
        fig.set__legend()
        fig.save__figure()

    # ------------------------------------------------- #
    # --- [5] charge C                              --- #
    # ------------------------------------------------- #
    config_  = {
        "figure.pngFile" : os.path.join( pngDir, "stat__s-{0}.png".format( "charge_C" ) ), 
        "ax1.y.label"    : ylabels["charge_C"],
    }
    config = { **config, **config_ }
    fig    = gp1.gplot1D( config=config )
    fig.add__plot( xAxis=data["s"], yAxis=data["charge_C"] )
    fig.set__axis()
    fig.save__figure()

    

# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    inpFile = "impactx/diags/reduced_beam_characteristics.0"
    plot__statistics( inpFile=inpFile )
