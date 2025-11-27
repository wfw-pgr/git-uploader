import os, sys, json5
import pandas as pd
import numpy  as np
import nk_toolkit.impactx.impactx_toolkit as itk


# ========================================================= #
# ===  get__particles.py                                === #
# ========================================================= #

def get__particles( paramsFile="dat/parameters.json" ):

    # ------------------------------------------------- #
    # --- [1] functions                             --- #
    # ------------------------------------------------- #
    def step_mapping( step_bpm ):
        return( (step_bpm-1)*2 )
    
    # ------------------------------------------------- #
    # --- [2] load data                             --- #
    # ------------------------------------------------- #
    with open( paramsFile, "r" ) as f:
        params = json5.load( f )
    bpm     = itk.load__impactHDF5( inpFile=params["file.bpm"] ).reset_index( drop=True )
    ref     = pd.read_csv( params["file.ref"], sep=r"\s+" )

    # ------------------------------------------------- #
    # --- [3] concatenate ref / particle data       --- #
    # ------------------------------------------------- #
    ref_df  = ref.loc[ step_mapping( bpm["step"] ), : ]
    slist   = [ "s","beta","gamma", "x","y","z","t", "px","py","pz","pt" ]
    renames = { s:"ref_"+s for s in slist }
    ref_df  = ( ref_df[ slist ] ).rename( columns=renames ).reset_index( drop=True )
    bpm     = pd.concat( [ bpm, ref_df ], axis=1 )
    return( bpm )


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    bpm = get__particles()
    print( bpm )
