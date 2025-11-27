import os, sys, json5, re
import numpy          as np
import pandas         as pd

# ========================================================= #
# ===  translate__impactxRFcavity.py                    === #
# ========================================================= #

def translate__impactxRFcavity( paramsFile="dat/parameters.json", \
                                beamlineFile="dat/beamline.json",
                                outFile="dat/beamline_.json", phaseFile="dat/rfphase.csv" ):

    # ------------------------------------------------- #
    # --- [1] load files                            --- #
    # ------------------------------------------------- #
    with open( paramsFile, "r" ) as f:
        params   = json5.load( f )
    with open( beamlineFile, "r" ) as f:
        beamline = json5.load( f )
    sequence = beamline["sequence"]
    elements = beamline["elements"]

    # ------------------------------------------------- #
    # --- [2] guess phase routine                   --- #
    # ------------------------------------------------- #
    def guess__RFcavityPhase( elements=None, params=None, phaseFile=None ):

        amu = 931.494       # [MeV]
        cv  = 299792458.0   # light of speed [m/s]
        
        # ------------------------------------------------- #
        # --- [2-1] use functions                       --- #
        # ------------------------------------------------- #
        def norm_angle( deg ):
            deg  = np.asarray( deg, dtype=float )
            ret  = ( ( deg + 180.0 ) % 360.0 ) - 180.0
            if ( np.ndim(ret) == 0 ): ret = float( ret )
            return( ret )
    
        # ------------------------------------------------- #
        # --- [2-2] guess initial rfcavity phase        --- #
        # ------------------------------------------------- #
        Ek0         = params["beam.Ek.MeV/u"] * params["beam.u"]
        Em0         = params["beam.mass.amu"] * amu
        omega       = params["beam.freq"] * 2.0 * np.pi
        df          = pd.DataFrame.from_dict( elements, orient="index" )
        df          = df.drop( columns=[ "k","aperture_x", "aperture_y", "harmonics" ] )
        df["ds"]    = params["translate.cavity.length"]
        egain       = ( df["volt"] * np.cos( df["phase"] /180.0*np.pi ) ).fillna(0)    
        Ek_in       = np.concatenate( ([0.0], np.cumsum(egain)[:-1]) ) + Ek0
        Ek_out      = np.cumsum( egain ) + Ek0
        df["Ek"]    = 0.5*( Ek_in + Ek_out )
        df["gamma"] = 1.0 + df["Ek"] / Em0
        df["beta"]  = np.sqrt( 1.0 - 1.0/df["gamma"]**2 )
        vp          = df["beta"] * cv
        dt          = df["ds"].to_numpy() / vp.to_numpy()
        t_in        = np.concatenate( ([0.0], np.cumsum(dt)[:-1] ) )
        t_out       = t_in + dt
        t_mid       = 0.5*( t_in + t_out )
        df["tpass"] = t_mid
        df["phi_o"] = norm_angle( t_mid * omega / np.pi * 180.0 )
        df["phi_t"] = norm_angle( params["translate.cavity.phase"] )
        df["phi_c"] = norm_angle( df["phi_t"] - df["phi_o"] )
        df["phi_b"] = 0.0
        
        # ------------------------------------------------- #
        # --- [2-3] return                              --- #
        # ------------------------------------------------- #
        if ( phaseFile is not None ):
            df.to_csv( phaseFile )
        return( df )

    # ------------------------------------------------- #
    # --- [3] convert routine                       --- #
    # ------------------------------------------------- #
    def convert__rfcavity( element, params, phase_df ):
        amu    = 931.494  # [MeV]
        Em0    = params["beam.mass.amu"] * amu
        ds     = params["translate.cavity.length"]
        freq   = params["beam.freq"] * element["harmonics"]
        escale = element["volt"] / ds / Em0
        phase  = phase_df["phi_c"].loc[ element["name"] ]
        ret    = { "type":element["type"], "name":element["name"], "ds":ds, "escale":escale, \
                   "freq":freq, "phase":phase, \
                   "aperture_x":element["aperture_x"], "aperture_y":element["aperture_y"] } 
        return( ret )
    
    # ------------------------------------------------- #
    # --- [2] call converter                        --- #
    # ------------------------------------------------- #
    phase_df  = guess__RFcavityPhase( elements=elements, params=params, phaseFile=phaseFile )
    elements_ = {}
    for key in sequence:
        if ( elements[key]["type"].lower() in [ "rfcavity" ] ):
            elements_[key] = convert__rfcavity( elements[key], params, phase_df )
        else:
            elements_[key] = elements[key]

    # ------------------------------------------------- #
    # --- [3] save and return                       --- #
    # ------------------------------------------------- #
    beamline["elements"] = elements_
    with open( outFile, "w" ) as f:
        json5.dump( beamline, f, indent=2 )
    return(beamline)



# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    translate__impactxRFcavity()
