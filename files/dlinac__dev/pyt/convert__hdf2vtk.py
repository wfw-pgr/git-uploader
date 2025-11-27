import os, sys
import h5py
import numpy   as np
import pandas  as pd
import pyvista as pv


# ========================================================= #
# === load__impactHDF5.py                               === #
# ========================================================= #

def load__impactHDF5( inpFile=None, pids=None, steps=None, random_choice=None, 
                      redefine_pid=True, redefine_step=True ):

    # ------------------------------------------------- #
    # --- [1] load HDF5 file                        --- #
    # ------------------------------------------------- #
    stack = {}
    with h5py.File( inpFile, "r" ) as f:
        steps = sorted( [ int( key ) for key in f["data"].keys() ] )
        for step in steps:
            key, df    = str(step), {}
            df["pid"]  = f["data"][key]["particles"]["beam"]["id"][:]
            df["xp"]   = f["data"][key]["particles"]["beam"]["position"]["x"][:]
            df["yp"]   = f["data"][key]["particles"]["beam"]["position"]["y"][:]
            df["tp"]   = f["data"][key]["particles"]["beam"]["position"]["t"][:]
            df["px"]   = f["data"][key]["particles"]["beam"]["momentum"]["x"][:]
            df["py"]   = f["data"][key]["particles"]["beam"]["momentum"]["y"][:]
            df["pz"]   = f["data"][key]["particles"]["beam"]["momentum"]["t"][:]
            df["step"] = np.full( df["pid"].shape, step, dtype=int )
            stack[key] = pd.DataFrame( df )
    ret = pd.concat( stack, ignore_index=True )
    
    # ------------------------------------------------- #
    # --- [2] return                                --- #
    # ------------------------------------------------- #
    if ( redefine_pid  ):
        ret["pid"]  = pd.factorize( ret["pid"]  )[0] + 1
    if ( redefine_step ):
        ret["step"] = pd.factorize( ret["step"] )[0] + 1
    if ( random_choice is not None ):
        npart = len( set( ret["pid"] ) )
        if random_choice > npart:
            raise ValueError( f"random_choice ({random_choice}) > number of particles ({npart})")
        pids  = np.random.choice( np.arange(1,npart+1), size=random_choice, replace=False )
    if ( pids  is not None ):
        ret   = ret[ ret["pid"].isin( pids ) ]
    if ( steps is not None ):
        ret   = ret[ ret["step"].isin( steps ) ]
    return( ret )


# ========================================================= #
# ===  convert__hdf2vtk.py                              === #
# ========================================================= #

def convert__hdf2vtk( hdf5File=None, outFile=None, \
                      pids=None, steps=None, random_choice=None ):

    # ------------------------------------------------- #
    # --- [1] arguments check                       --- #
    # ------------------------------------------------- #
    if ( os.path.exists( hdf5File ) ):
        Data = load__impactHDF5( inpFile=hdf5File, random_choice=random_choice, \
                                 pids=pids, steps=steps )
    else:
        raise FileNotFoundError( f"[ERROR] HDF5 File not Found :: {hdf5File}" )
    if ( outFile is None ):
        raise TypeError( f"[ERROR] outFile == {outFile} ???" )
    else:
        ext = os.path.splitext( outFile )[1]

    # ------------------------------------------------- #
    # --- [2] save as vtk poly data                 --- #
    # ------------------------------------------------- #
    steps = sorted( Data["step"].unique() )

    for ik,step in enumerate(steps):
        # -- points coordinate make -- #
        df     = Data[ Data["step"] == step ]
        coords = df[ ["xp", "yp", "tp"] ].to_numpy()
        cloud  = pv.PolyData( coords )
        # -- momentum & pid -- #
        cloud.point_data["pid"]      = df["pid"].to_numpy()
        cloud.point_data["momentum"] = df[ ["px", "py", "pz"] ].to_numpy()
    
        # -- save file -- #
        houtFile = outFile.replace( ext, "-{0:06}".format(ik+1) + ext )
        cloud.save( houtFile )
        print( "[convert__hdf2vtk.py] outFile :: {} ".format( houtFile ) )
    return()
        

# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    hdf5File = "impactx/diags/openPMD/bpm.h5"
    outFile  = "png/out.vtp"
    ret      = convert__hdf2vtk( hdf5File=hdf5File, outFile=outFile )






