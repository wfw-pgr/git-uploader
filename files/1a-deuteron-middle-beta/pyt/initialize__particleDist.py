import json5, os, sys
import pandas                       as pd
import numpy                        as np
import matplotlib.cm                as cm
import matplotlib.colors            as mc
import nk_toolkit.plot.load__config as lcf
import nk_toolkit.plot.gplot2D      as gp2

# ========================================================= #
# ===  initialize__particleDist.py                      === #
# ========================================================= #

def initialize__particleDist():

    mm, mrad = 1.e-3, 1.e-3
    
    # ------------------------------------------------- #
    # --- [1] parameters                            --- #
    # ------------------------------------------------- #
    inpFile = "dat/parameters.json"
    with open( inpFile, "r" ) as f:
        params = json5.load( f )
    cmd = "start"
    if ( params["ptc.sw"] ): cmd = "ptc_start"
    
    # ------------------------------------------------- #
    # --- [2] calculation                           --- #
    # ------------------------------------------------- #
    npt      = params["init.npt"]
    gamma    = 1.0 + params["init.Ek"] / ( params["mass/u"]*params["umass"] ) # -- gamma = 1+Ek/E0
    beta     = np.sqrt( 1.0 + 1.0 / gamma**2 )
    emit_n   = params["init.emit_n"] * np.pi * mm * mrad
    emit_x   = emit_n * beta * gamma
    emit_y   = emit_n * beta * gamma
    emit_z   = emit_n * beta * gamma
    beta_x   = params["init.beta_x"]
    beta_y   = params["init.beta_y"]
    beta_z   = params["init.beta_z"]
    sigma_xp = np.sqrt( beta_x * emit_x )
    sigma_px = np.sqrt( emit_x / beta_x )
    sigma_yp = np.sqrt( beta_y * emit_y )
    sigma_py = np.sqrt( emit_y / beta_y )
    sigma_zp = np.sqrt( beta_z * emit_z )
    sigma_pz = np.sqrt( emit_z / beta_z )
    xp       = np.random.normal( 0, sigma_xp, npt )
    px       = np.random.normal( 0, sigma_px, npt )
    yp       = np.random.normal( 0, sigma_yp, npt )
    py       = np.random.normal( 0, sigma_py, npt )
    zp       = np.random.normal( 0, sigma_zp, npt )
    pz       = np.random.normal( 0, sigma_pz, npt )

    # ------------------------------------------------- #
    # --- [3] write data                            --- #
    # ------------------------------------------------- #
    with open( params["file.start"], "w" ) as f:
        for ik in list( range( npt ) ):
            f.write( "{0}, x={1}, px={2}, y={3}, py={4}, t={5}, pt={6};\n"\
                     .format( cmd, xp[ik], px[ik], yp[ik], py[ik], zp[ik], pz[ik] ) )
        print( "[initialize__particleDist.py] output = {} ".format( params["file.start"] ) )

    # ------------------------------------------------- #
    # --- [4] save as a dat File & display          --- #
    # ------------------------------------------------- #
    df = pd.DataFrame( { "xp": xp, "px": px, "yp": yp, "py": py, "zp": zp, "pz": pz } )
    df.to_hdf( params["file.init.hdf"], key="data" )
    print( "[initialize__particleDist.py] output = {} ".format( params["file.init.hdf"] ) )
    print()
    display()


# ========================================================= #
# ===  display initial distribution                     === #
# ========================================================= #

def display(  ):

    x_, y_, z_   = 0, 1, 2
    mm, mrad     = 1.0e-3, 1.0e-3

    # ------------------------------------------------- #
    # --- [1] load file                             --- #
    # ------------------------------------------------- #
    inpFile = "dat/parameters.json"
    with open( inpFile, "r" ) as f:
        params = json5.load( f )
    Data                   = pd.read_hdf( params["file.init.hdf"] )
    Data["xp"], Data["yp"] = Data["xp"]/mm  , Data["yp"]/mm
    Data["px"], Data["py"] = Data["px"]/mrad, Data["py"]/mrad

    # ------------------------------------------------- #
    # --- [2] Display Data                          --- #
    # ------------------------------------------------- #
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [4.5,4.5],
        "figure.position"    : [ 0.16, 0.16, 0.84, 0.84 ],
        "ax1.x.minor.nticks" : 1,
        "cmp.level"          : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "cmp.colortable"     : "jet",
        "cmp.transparent"    : [ 0.01, None ], 
        "cmp.cmpmode"        : "pcolormesh",
    }
    config = { **config, **config_ }
    
    range_xy = { "auto":False, "min": -60.0, "max":+60.0, "num":7 }
    range_p  = { "auto":False, "min": -20.0, "max":+20.0, "num":9 } 
    plotsets = [ { "key1":"xp", "key2":"yp", "label.x":r"$x$ [mm]", "label.y":r"$y$ [mm]",
                   "range.x":range_xy, "range.y":range_xy },
                 { "key1":"xp", "key2":"px", "label.x":r"$x$ [mm]", "label.y":r"$p_x$ [mrad]",
                   "range.x":range_xy, "range.y":range_p  },
                 { "key1":"yp", "key2":"py", "label.x":r"$y$ [mm]", "label.y":r"$p_y$ [mrad]",
                   "range.x":range_xy, "range.y":range_p  },
                 { "key1":"px", "key2":"py", "label.x":r"$p_x$ [mm]", "label.y":r"$p_y$ [mrad]",
                   "range.x":range_p , "range.y":range_p  },
    ]
    for ik, pset in enumerate( plotsets ):
        key1, key2 = pset["key1"], pset["key2"]
        config_ = {
            "figure.pngFile" : params["init.plot.pngFile"].format( key1, key2 ),
            "ax1.x.label"    : pset["label.x"], 
            "ax1.y.label"    : pset["label.y"], 
            "ax1.x.range"    : pset["range.x"],
            "ax1.y.range"    : pset["range.y"],
        }
        config = { **config, **config_ }
        hist, xe, ye  = np.histogram2d( Data[key1], Data[key2],\
                                        bins=params["init.plot.nbins"] )
        xa, ya        = 0.5*( xe[1:]+xe[:-1] ), 0.5*( ye[1:]+ye[:-1] )
        xg, yg        = np.meshgrid( xa, ya )
        hist          = hist / np.max( hist )      #  -- normalization --  #
        fig           = gp2.gplot2D( xAxis=xg, yAxis=yg, cMap=hist.T, config=config )
    
    
# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    initialize__particleDist()    
