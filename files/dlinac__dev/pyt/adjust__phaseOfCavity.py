import os, sys, json5
import numpy  as np
import pandas as pd
import nk_toolkit.impactx.impactx_toolkit as itk


# ========================================================= #
# ===  adjust__phaseOfCavity.py                         === #
# ========================================================= #

def adjust__phaseOfCavity( paramsFile="dat/parameters.json", steps=None, pids=None, \
                           elementsFile="impactx/beamline.json", outFile="dat/adjust_phase.csv" ):

    cv = 2.997e8
    
    # ------------------------------------------------- #
    # --- [1] load data                             --- #
    # ------------------------------------------------- #
    with open( paramsFile , "r" ) as f:
        params   = json5.load( f )
    with open( elementsFile, "r" ) as f:
        elements = json5.load( f )
    refp     = pd.read_csv( "impactx/diags/ref_particle.0", sep=r"\s+" )
    ptcls    = itk.get__particles( paramsFile=paramsFile, steps=steps, pids=pids )
    step_bpm = np.sort( np.unique( ptcls["step"].astype( int ) ) )

    # ------------------------------------------------- #
    # --- [2] functions to use                      --- #
    # ------------------------------------------------- #
    def normalize__degree( degree ):
        return( ( degree + 180.0 )%(360.0) - 180.0 )
    
    # ------------------------------------------------- #
    # --- [3] extract rf component to adjust        --- #
    # ------------------------------------------------- #
    stack   = []
    rfList  = [ "rfcavity", "shortrf" ]
    rfElems = [ int(key) for key,elem in elements.items() if ( elem["type"].lower() in rfList ) ]
    phi_t   = params["translate.cavity.phase"]
    for step_rf in rfElems:
        name   = elements[ str(step_rf) ]["name"]
        ibpm1  = np.max( step_bpm[ step_bpm <= step_rf ] )
        ibpm2  = np.min( step_bpm[ step_bpm >= step_rf ] )
        tp1    = ( ( ptcls[ ptcls["step"] == ibpm1 ] ).set_index( "pid" ) )["tp"]
        tp2    = ( ( ptcls[ ptcls["step"] == ibpm2 ] ).set_index( "pid" ) )["tp"]
        t_rf   = np.sort( ( ( 0.5 * ( tp1 + tp2 ) ).dropna() ).to_numpy() )
        if ( len( t_rf ) == 0 ):
            stack += [ [ name, step_rf, np.nan, phi_t, np.nan ] ]
            continue
        else:
            s1,s2  = np.percentile( t_rf, [ 16.0, 84.0 ] )
        t_avg     = np.average( t_rf[ np.where( ( t_rf > s1 ) & ( t_rf < s2 ) ) ] )
        t_ref     = refp.iloc[ step_rf ].loc["t"]
        t_tot     = t_ref - t_avg
        t_tot_s   = t_tot / cv
        phi_p     = 360.0 * params["beam.freq.Hz"] * params["beam.harmonics"] * t_tot_s
        phi_p     = normalize__degree( phi_p )
        phi_t     = normalize__degree( phi_t )
        phi_c     = normalize__degree( phi_t - phi_p )
        stack    += [ [ name, step_rf, phi_p, phi_t, phi_c ] ]
        # print( t_avg, t_ref, t_tot, phi_t, phi_p, phi_c )
        # sys.exit()
    phi = pd.DataFrame( np.array( stack ), columns=[ "name", "step", "phi_p", "phi_t", "phi_c"] )

    # ------------------------------------------------- #
    # --- [4] save and return                       --- #
    # ------------------------------------------------- #
    if ( outFile is not None ):
        phi.to_csv( outFile, index=False )
    return( phi )


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    adjust__phaseOfCavity()

    
