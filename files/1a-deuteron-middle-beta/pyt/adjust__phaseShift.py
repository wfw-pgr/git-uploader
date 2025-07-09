import os, sys, json5, re, io
import numpy  as np
import pandas as pd

import nk_toolkit.madx.load__tfs      as ltf
import nk_toolkit.plot.load__config   as lcf
import nk_toolkit.plot.gplot1D        as gp1

# ========================================================= #
# ===  prepare__referenceParticle.py                    === #
# ========================================================= #

def prepare__referenceParticle():

    # ------------------------------------------------- #
    # --- [1] load parameters                       --- #
    # ------------------------------------------------- #
    inpFile = "dat/parameters.json"
    with open( inpFile, "r" ) as f:
        params = json5.load( f )
    cmd = "start"
    if ( params["ptc.sw"] ): cmd = "ptc_start"

    # ------------------------------------------------- #
    # --- [2] start file                            --- #
    # ------------------------------------------------- #
    with open( params["file.start"], "w" ) as f:
        f.write( "{0}, x=0, px=0, y=0, py=0, t=0, pt=0;\n".format( cmd ) )
        print( "[initialize__particleDist.py] output = {} ".format( params["file.start"] ) )

    return()



# ========================================================= #
# ===  plot phase                                       === #
# ========================================================= #
def plot__phaseShift():
    
    # ------------------------------------------------- #
    # --- [1] load track data                       --- #
    # ------------------------------------------------- #
    ret = extract__phaseAtRFgap()
    
    # ------------------------------------------------- #
    # --- [2] plot phase                            --- #
    # ------------------------------------------------- #
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [4.5,4.5],
        "figure.pngFile"     : "png/phase.png", 
        "figure.position"    : [ 0.16, 0.16, 0.94, 0.94 ],
        "ax1.y.normalize"    : 1.0e0, 
        "ax1.x.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.y.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.x.label"        : "S [m]",
        "ax1.y.label"        : "phase (deg.)",
        "ax1.x.minor.nticks" : 1, 
        "plot.marker"        : "o",
        "plot.markersize"    : 3.0,
        "legend.fontsize"    : 9.0, 
    }
    config = { **config, **config_ }
    
    fig    = gp1.gplot1D( config=config )
    fig.add__plot( xAxis=ret["S"], yAxis=ret["SHIFT"], label="shift" )
    fig.add__plot( xAxis=ret["S"], yAxis=ret["PHASE"], label="phase" )
    fig.set__axis()
    fig.save__figure()
    return()


# ========================================================= #
# ===  extract__phaseAtRFgap                            === #atrf
# ========================================================= #

def extract__phaseAtRFgap( inpFile="dat/parameters.json" ):

    MHz = 1.0e6

    # ------------------------------------------------- #
    # --- [1] load parameters / trackData           --- #
    # ------------------------------------------------- #
    with open( inpFile, "r" ) as f:
        params = json5.load( f )
    track = load__trackData( trackFile=params["post.track.inpFile"] )

    # ------------------------------------------------- #
    # --- [2] extract particles at RFgap            --- #
    # ------------------------------------------------- #
    keys   = [ key for key in track.keys() if ( re.match( r"[rR][fF][0-9]+", key ) ) ]
    items  = [ "X","PX","Y","PY","T","PT","S","E" ]
    rows   = []
    for key in keys:
        avgs        = ( track[key] )[items].mean()
        row         = avgs.to_frame().T
        row["NAME"] = key
        rows       += [ row ]
    df    = pd.concat( rows, ignore_index=True )
    items = ["NAME"] + items
    df    = df[ items ]

    # ------------------------------------------------- #
    # --- [3] calculate phase                       --- #
    # ------------------------------------------------- #
    freq        = params["harmonics"] * params["freq_0"] * MHz
    shift       = 2.0*np.pi*freq/params["cv"]* df["T"]
    df["PHASE"] = 0.0
    df["SHIFT"] = 180.0/np.pi * shift
    df.to_csv( params["file.phase"] )
    return( df )


# ========================================================= #
# ===  load__trackData                                  === #
# ========================================================= #

def load__trackData( trackFile="madx/out/track.tfsone" ):

    # ------------------------------------------------- #
    # --- [1] load particle info                    --- #
    # ------------------------------------------------- #
    comment_marks = ( "@", "$" )
    with open( trackFile, "r" ) as f:
        lines = [ line for line in f if not( line.strip().startswith( comment_marks ) ) ]
    line   = lines.pop(0)
    smatch = re.match( r"^\*(.+)$", line )
    if ( smatch ):
        columns = ( smatch.group(1) ).strip().split()
    else:
        sys.exit( "no match... no columns ERROR." )

    # ------------------------------------------------- #
    # --- [2] store dataframe by segment            --- #
    # ------------------------------------------------- #
    ret, key, sbuff = {}, None, []
    for line in lines:
        if ( line.startswith( "#segment" ) ):
            if ( key and sbuff ):
                ret[key] = pd.DataFrame( sbuff, columns=columns )
                ret[key] = ret[key].apply( pd.to_numeric )
                sbuff    = []
            key      = line.strip().split()[-1]
        else:
            sbuff   += [ line.split() ]
    #  -- last element -- #
    if ( key and sbuff ):
        ret[key] = pd.DataFrame( sbuff, columns=columns )
        ret[key] = ret[key].apply( pd.to_numeric )
    return( ret )


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    # prepare__referenceParticle()
    plot__phaseShift()
    
