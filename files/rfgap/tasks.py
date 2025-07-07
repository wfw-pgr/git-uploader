import os, sys, glob, invoke, json5
import cpymad.madx
import numpy  as np
import pandas as pd
import nk_toolkit.madx.load__tfs as ltf

# ========================================================= #
# ===  madx command                                     === #
# ========================================================= #
@invoke.task( help={ 'file': '.madx file == input file.'} )
def madx( c, file="main.madx", wrkdir="madx/" ):
    """execute madx calculation."""
    os.chdir( wrkdir )
    
    # ------------------------------------------------- #
    # --- [1] file check                            --- #
    # ------------------------------------------------- #
    if not( os.path.exists(file) ):
        filelist = glob.glob( "./*.madx" )
        if ( len(filelist) == 1 ):
            file = filelist[0]
            print( f" following .madx file will be used... :: {file}" )
        else:
            sys.exit(" cannot find input file :: {}".format( file ))
    else:
        print( f"\n --- input : {file} --- \n" )
        
    # ------------------------------------------------- #
    # --- [2] execute madx                          --- #
    # ------------------------------------------------- #
    m = cpymad.madx.Madx()
    try:
        m.call( file )
        print( "\n --- End of Execution --- \n" )
    except:
        print( "Error" )
    os.chdir( "../" )
    return()


# ========================================================= #
# ===  initialization                                   === #
# ========================================================= #
@invoke.task
def init( c ):
    """initialization of madx."""

    # ------------------------------------------------- #
    # --- [1] initialize                            --- #
    # ------------------------------------------------- #
    print( "\n\n[initialize__particleDist.py]\n" )
    import pyt.initialize__particleDist as ipd
    ipd.initialize__particleDist()
    # ------------------------------------------------- #
    # --- [2] translate track => madx               --- #
    # ------------------------------------------------- #
    print( "\n\n[translate__track2madx.py]\n" )
    import pyt.translate__track2madx as ttm
    ttm.translate__track2madx()
    return()
    

# ========================================================= #
# ===  post command                                     === #
# ========================================================= #
@invoke.task
def post( c, paramsFile="dat/parameters.json" ):
    """post analysis, like plot."""

    # ------------------------------------------------- #
    # --- [1] load paramsFile                       --- #
    # ------------------------------------------------- #
    with open( paramsFile, "r" ) as f:
        params = json5.load( f )
    
    # ------------------------------------------------- #
    # --- [2] twiss -> beam size sigma              --- #
    # ------------------------------------------------- #
    if ( params["post.twiss.sw"] ):
        import pyt.postProcess__twiss as ptw
        twiss  = ptw.postProcess__twiss( paramsFile=paramsFile )
    if ( params["post.track.sw"] ):
        import pyt.postProcess__track as ptr
        track  = ptr.postProcess__track( paramsFile=paramsFile )
    
    # ------------------------------------------------- #
    # --- [3] compare with track-v38's data         --- #
    # ------------------------------------------------- #
    if ( params["post.compare.sw"] ):
        import pyt.compare__track_madx as ctm
        ret    = ctm.compare__track_madx()
    
    # ------------------------------------------------- #
    # --- [?] execute post analysis                 --- #
    # ------------------------------------------------- #
    # #  -- plotly -- #
    # survey     = ltf.load__tfs( tfsFile=surveyFile )
    # twiss      = ltf.load__tfs( tfsFile= twissFile )
    # pbl.plotly__beamline( survey=survey, twiss=twiss, html=html )
    return()


# ========================================================= #
# ===  data compress                                    === #
# ========================================================= #
@invoke.task
def compress( c ):
    """compress .tfs data"""
    # ------------------------------------------------- #
    # --- [1] file search                           --- #
    # ------------------------------------------------- #
    files1 = glob.glob( "madx/out/*.tfs"    )
    files2 = glob.glob( "madx/out/*.tfsone" )
    files  = files1 + files2
    # ------------------------------------------------- #
    # --- [2] compress                              --- #
    # ------------------------------------------------- #
    for ifile in files:
        contents = ltf.load__tfs( tfsFile=ifile )
        ofile    = os.path.splitext( ifile )[0] + ".h5"
        contents["df"].to_hdf( ofile, key="data" )
        print( " output -- {}".format( ofile ) )
    return()

    
# ========================================================= #
# ===  clean command                                    === #
# ========================================================= #
@invoke.task
def clean(c, wrkdir="madx", outdir="out" ):
    """clean madx outputs."""
    os.chdir( wrkdir )
    deleted    = 0

    # ------------------------------------------------- #
    # --- [1] delete results                        --- #
    # ------------------------------------------------- #
    extensions = [ ".tfs", ".tfsone", ".h5" ]
    for dfile in glob.glob( "out/*" ):
        if any( dfile.endswith( ext ) for ext in extensions ):
            os.remove( dfile )
            deleted += 1
            print( "  -- delete  :: {} ".format( dfile ) )

    # ------------------------------------------------- #
    # --- [2] delete intermediates                  --- #
    # ------------------------------------------------- #
    intermediates = [ "checkpoint_restart.dat", "internal_mag_pot.txt" ]
    filelist      = glob.glob( "./*" )
    for dfile in filelist:
        if ( os.path.basename(dfile) in intermediates ):
            os.remove( dfile )
            deleted += 1
            print( "  -- delete  :: {} ".format( dfile ) )

    # ------------------------------------------------- #
    # --- [3] return                                --- #
    # ------------------------------------------------- #
    print( f"\n --- deleted :: {deleted} files --- \n" )
    os.chdir( "../" )
    return()


# ========================================================= #
# ===  all command                                      === #
# ========================================================= #
@invoke.task(pre=[clean, init, madx, post])
def all(c):
    """all command"""    
    print( "  --- clean, madx, plot command is done --- " )
