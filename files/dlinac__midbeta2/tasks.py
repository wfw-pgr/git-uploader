import os, sys, re, glob, subprocess, shutil, json5
import invoke
import pandas as pd
import numpy  as np
import nk_toolkit.impactx.io_toolkit               as itk
import nk_toolkit.impactx.plot_toolkit             as ptk
import nk_toolkit.impactx.analyze_toolkit          as atk
import nk_toolkit.impactx.match_toolkit            as mtk
import nk_toolkit.impactx.translate__track2impactx as t2i


# ========================================================= #
# ===  execute impactx                                  === #
# ========================================================= #
@invoke.task
def run( ctx, logFile="impactx.log" ):
    """Run the ImpactX simulation."""
    cwd = os.getcwd()
    cmd = "python main_impactx.py"
    try:
        os.chdir( "impactx/" )
        with open("impactx.log", "w") as log:
            process = subprocess.Popen( cmd.split(), \
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, \
                text=True, bufsize=1 )
            for line in process.stdout:
                print( line, end="" )  # terminal stdout
                log.write( line )      # save in log file
        process.wait()
    finally:
        os.chdir( cwd )

        
# ========================================================= #
# ===  translate track -> impactx                       === #
# ========================================================= #
@invoke.task
def translate( ctx ):
    """initialize and prepare the ImpactX simulation."""
    t2i.translate__track2impactx( paramsFile   = "dat/parameters.json", \
                                  trackFile    = "track/sclinac.dat" , \
                                  impactxBLFile= "dat/beamline_impactx.json", \
                                  trackBLFile  = "dat/beamline_track.json", \
                                  phaseFile    = "dat/rfphase.csv" )

    
# ========================================================= #
# ===  adjust rf phase                                  === #
# ========================================================= #
@invoke.task
def adjust( ctx ):
    """initialize and prepare the ImpactX simulation."""
    mtk.match__rfphase()
    
    
# ========================================================= #
# ===  clean output files                               === #
# ========================================================= #
@invoke.task
def clean( ctx ):
    """Remove output files from previous runs."""
    patterns = [ "impactx/diags.old.*", "impactx/diags", "impactx/__pycache__",\
                 "png/*.png" ]
    for pattern in patterns:
        for path in glob.glob( pattern ):
            if os.path.isfile(path):
                print( f"Removing file {path}" )
                os.remove(path)
            elif os.path.isdir(path):
                print( f"Removing directory {path}" )
                shutil.rmtree(path)

                
# ========================================================= #
# ===  post analysis                                    === #
# ========================================================= #
@invoke.task
def post( ctx, \
          refp=False, stat=False, post=False, poincare=False, \
          trajectory=False, vtk=False, ext=None, pcnfFile="dat/visualize.json" ):
    """Run post-analysis script."""

    # ------------------------------------------------- #
    # --- [1] load config                           --- #
    # ------------------------------------------------- #
    with open( pcnfFile, "r" ) as f:
        plot_conf = json5.load( f )

    # ------------------------------------------------- #
    # --- [2] modify file extension                 --- #
    # ------------------------------------------------- #
    if ( ext is None ):
        ext  = os.environ.get( "IMPACTX_REFP_EXTENSION", ".0.0" )
    plot_conf["files"]["refp"] = re.sub( r"(\.\d+)+$", "", plot_conf["files"]["refp"] ) + ext
    plot_conf["files"]["stat"] = re.sub( r"(\.\d+)+$", "", plot_conf["files"]["stat"] ) + ext

    # ------------------------------------------------- #
    # --- [3] call general visualization routine    --- #
    # ------------------------------------------------- #
    vis = ptk.visualize__main( refp=refp, stat=stat, poincare=poincare, post=post, \
                               trajectory=trajectory, plot_conf=plot_conf )


# ========================================================= #
# ===  all = clean + run + post                         === #
# ========================================================= #
@invoke.task(pre=[clean, run, post])
def all(ctx):
    """Run all steps: clean, impact, post."""
    pass
