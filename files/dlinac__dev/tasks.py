import os, glob, subprocess, shutil, json5
import invoke
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
def post( ctx, paramsFile="dat/parameters.json", \
          refp=False, stat=True, trajectory=False, vtk=False, post=True, \
          poincare=False, ext=".0" ):
    """Run post-analysis script."""

    if ( paramsFile is not None ):
        with open( paramsFile, "r" ) as f:
            params = json5.load( f )
    else:
        params = { "plot.conf.refp":None, \
                   "plot.conf.stat":None, \
                   "plot.conf.traj":None  }
        
    # ------------------------------- #
    # --- [1] reference particle  --- #
    # ------------------------------- #
    if ( refp ):
        refpFile  = "impactx/diags/ref_particle" + ext
        ptk.plot__refparticle( inpFile=refpFile, plot_conf=params["plot.conf.refp"] )

    # ------------------------------- #
    # --- [2] statistics          --- #
    # ------------------------------- #
    if ( stat ):
        # statFile  = "impactx/diags/reduced_beam_characteristics" + ext
        # ptk.plot__statistics( inpFile=statFile, plot_conf=params["plot.conf.stat"]  )
        stat = itk.get__beamStats()
        itk.get__beamStats()
        ptk.plot__stats( stat=stat, plot_conf="dat/stat_conf.json" )

    # ------------------------------- #
    # --- [3] trajectory          --- #
    # ------------------------------- #
    if ( trajectory ):
        hdf5File      = "impactx/diags/openPMD/bpm.h5"
        refpFile      = "impactx/diags/ref_particle" + ext
        random_choice = 300
        ptk.plot__trajectories( hdf5File=hdf5File, refpFile=refpFile, \
                                random_choice=random_choice, plot_conf=params["plot.conf.traj"] )

    # ------------------------------- #
    # --- [4] convert to vtk      --- #
    # ------------------------------- #
    if ( vtk ):
        hdf5File = "impactx/diags/openPMD/bpm.h5"
        outFile  = "png/bpm.vtp"
        itk.convert__hdf2vtk( hdf5File=hdf5File, outFile=outFile )

    # ------------------------------------------------- #
    # --- [5] additional analysis                   --- #
    # ------------------------------------------------- #
    if ( post ):
        refpFile   = None   # auto 
        statFile   = None
        recoFile   = None
        plot_conf  = None
        postFile   = "impactx/diags/posts.csv"
        atk.get__postprocessed ( refpFile=refpFile, statFile=statFile, \
                                 recoFile=recoFile, postFile=postFile )
        ptk.plot__postprocessed( postFile=postFile, plot_conf=plot_conf )

    # ------------------------------------------------- #
    # --- [6] poincare plot                         --- #
    # ------------------------------------------------- #
    if ( poincare ):
        recoFile = None
        refpFile = None
        bpmsFile = None
        bpms     = itk.get__particles( recoFile=recoFile, refpFile=refpFile, \
                                       bpmsFile=bpmsFile )
        steps    = list( set( bpms["step"] ) )
        for step in steps:
            ptk.plot__poincare( bpms=bpms, step=step )

    return()


# ========================================================= #
# ===  all = clean + run + post                         === #
# ========================================================= #
@invoke.task(pre=[clean, run, post])
def all(ctx):
    """Run all steps: clean, impact, post."""
    pass
