import os, sys, json5, re, io
import cpymad.madx
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
    fig.set__axis()
    fig.save__figure()
    return( ret )


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
    if ( os.path.exists( params["file.phase"] ) ):
        phase = pd.read_csv( params["file.phase"] )
        phase = phase["PHASE"].values
    else:
        print( "no profile" )
        input()
        phase = 0.0

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
    shift_deg   = 180.0/np.pi * shift
    df["PHASE"] = phase + shift_deg
    df["SHIFT"] =         shift_deg
    df["KICK5"] = df["T"]
    df.to_csv( params["file.phase"], index=False )
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
                ret[key] = ret[key].apply( pd.to_numeric, errors='coerce' )
                sbuff    = []
            key      = line.strip().split()[-1]
        else:
            sbuff   += [ line.split() ]
    #  -- last element -- #
    if ( key and sbuff ):
        ret[key] = pd.DataFrame( sbuff, columns=columns )
        ret[key] = ret[key].apply( pd.to_numeric, errors='coerce' )
    return( ret )



# ========================================================= #
# ===  initialize__phaseFile                            === #
# ========================================================= #
def initialize__phaseFile():
    trackFile = "track/sclinac.dat"
    with open( trackFile, "r" ) as f:
        lines = f.readlines()
    nRFgap = 0
    for line in lines:
        line_ = line.split()
        if ( len( line_ ) > 0 ):
            if ( line_[1].lower() == "rfgap" ):
                nRFgap += 1
    columns    = [ "NAME", "X","PX","Y","PY","T","PT","S","E", "PHASE","SHIFT", "KICK5" ]
    df         = pd.DataFrame( 0.0, index=range(nRFgap), columns=columns )
    df["NAME"] = [ "rf{}".format( irf+1 ) for irf in range(nRFgap) ]
    df.to_csv( "dat/phase.dat", index=False )
    return()


# ========================================================= #
# ===  execute__madx                                    === #
# ========================================================= #
def execute__madx():
    os.chdir( "madx/" )
    madxFile = "main.madx"
    madx_obj = cpymad.madx.Madx()
    madx_obj.call( madxFile )
    os.chdir( "../" )
    print( "\n --- End of Execution --- \n" )
    


# ========================================================= #
# ===  auto__adjustphase                                === #
# ========================================================= #

def auto__adjustphase():

    import calculate__energy     as eng
    import translate__track2madx as t2m
    
    prepare__referenceParticle()
    initialize__phaseFile()

    Nloop = 7
    stack = []
    for ik in range( 1,Nloop+1 ):
        print( " Nloop == {}".format( ik ) )
        t2m.translate__track2madx()
        execute__madx()
        shifts  = plot__phaseShift()
        energy  = eng.calculate__energy()
        stack  += [ { "iLoop":ik, "shifts":shifts, "energy":energy } ]


    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [4.5,4.5],
        "figure.position"    : [ 0.16, 0.16, 0.94, 0.94 ],
        "ax1.x.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.y.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.x.label"        : "S [m]",
        "ax1.x.minor.nticks" : 1, 
        "plot.marker"        : "o",
        "plot.markersize"    : 3.0,
        "legend.fontsize"    : 9.0, 
    }
    config   = { **config, **config_ }
    config_p = {
        "ax1.y.label"        : "phase (deg.)",        
        "figure.pngFile"     : "png/phase_loop.png",
    }
    config_e = {
        "ax1.y.label"        : "$E_k (MeV)$",        
        "figure.pngFile"     : "png/energy_loop.png",
    }
    config_p = { **config, **config_p }
    config_e = { **config, **config_e }
    
    fig1    = gp1.gplot1D( config=config_p )
    fig2    = gp1.gplot1D( config=config_e )
    for ik,dic in enumerate(stack):
        fig1.add__plot( xAxis=dic["shifts"]["S"], yAxis=dic["shifts"]["SHIFT"], \
                        label="iLoop={}".format(ik+1), color="C{}".format(ik+1)  )
        fig1.add__plot( xAxis=dic["shifts"]["S"], yAxis=dic["shifts"]["PHASE"], \
                        label="iLoop={}".format(ik+1), color="C{}".format(ik+1), \
                        linestyle="--"  )
        fig2.add__plot( xAxis=dic["energy"]["sL"], yAxis=dic["energy"]["Ek"], \
                        label="iLoop={}".format(ik+1) )
    fig1.set__axis()
    fig2.set__axis()
    fig1.set__legend()
    fig2.set__legend()
    fig1.save__figure()
    fig2.save__figure()
    return()


    

# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    
    # prepare__referenceParticle()
    # plot__phaseShift()
    
    auto__adjustphase()
    
