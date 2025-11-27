import os, sys, json5
import pandas as pd
import numpy  as np
import nk_toolkit.impactx.impactx_toolkit as itk


# ========================================================= #
# ===  get__energy.py                                   === #
# ========================================================= #

def get__energy( paramsFile="dat/parameters.json" ):

    amu = 931.494

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
    bpm   = itk.load__impactHDF5( inpFile=params["file.bpm"] )
    ref   = pd.read_csv( params["file.ref"], sep=r"\s+" )

    # ------------------------------------------------- #
    # --- [3] get energy                            --- #
    # ------------------------------------------------- #
    Em0       = params["beam.mass.amu"] * amu
    Ek0       = params["beam.Ek.MeV/u"] * params["beam.u"]
    Et0       = Em0 + Ek0
    p0c       = np.sqrt( Et0**2 - Em0**2 )
    gamma     = ref.loc[ step_mapping( bpm["step"] ), "gamma" ].to_numpy()
    Ek_ref    = ( gamma - 1.0 ) * Em0
    Ek        = Ek_ref + p0c * bpm["pt"].to_numpy()
    bpm["Ek"] = Ek
    return( bpm )


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #
if ( __name__=="__main__" ):
    bpm = get__energy()
    print( bpm )
