import os, sys, json5, re
import numpy          as np
import pandas         as pd

# ========================================================= #
# ===  translate__track2impactx.py                      === #
# ========================================================= #

def translate__track2impactx( paramsFile   ="dat/parameters.json", \
                              trackFile    ="track/sclinac.dat", \
                              impactxBLFile="dat/beamline_impactx.json", \
                              trackBLFile  ="dat/beamline_track.json", \
                              phaseFile    ="dat/rfphase.csv" ):

    ret = extract__trackv38_beamline( trackFile    =trackFile, \
                                      trackBLFile  =trackBLFile )
    ret = translate__impactxElements( paramsFile   =paramsFile, \
                                      trackBLFile  =trackBLFile, \
                                      impactxBLFile=impactxBLFile, \
                                      phaseFile    =phaseFile )
    return()
    

# ========================================================= #
# ===  extract__trackv38_beamline.py                    === #
# ========================================================= #

def extract__trackv38_beamline( trackFile="track/sclinac.dat", \
                                trackBLFile="dat/beamline_track.json" ):
    
    # ------------------------------------------------- #
    # --- [1] read track file                       --- #
    # ------------------------------------------------- #
    with open( trackFile, "r" ) as f:
        lines  = f.readlines()

    # ------------------------------------------------- #
    # --- [2] convert_quad                          --- #
    # ------------------------------------------------- #
    def convert_to_quad( words, counts ):
        
        MeV   = 1.0e+6
        cm    = 1.0e-2
        gauss = 1.0e-4
        
        name  = "qm{}".format( (counts["Nqm"]+1) )
        Bq    = float(words[2]) * gauss
        Ra    = float(words[5]) * cm
        ds    = float(words[4]) * cm
        gradB = Bq / Ra
        K1    = gradB
        ret   = [ { "type":"quadrupole", "name":name, "ds":ds, "k":K1, \
                    "aperture_x":Ra, "aperture_y":Ra } ]
        counts["Nqm"] += 1
        counts["at"]  += ds
        return( ret )

    # ------------------------------------------------- #
    # --- [3] convert_to_drift                      --- #
    # ------------------------------------------------- #
    def convert_to_drift( words, counts ):
        
        cm             = 1.0e-2
        
        name           = "dr{}".format( (counts["Ndr"]+1) )
        ds             = float(words[2]) * cm
        Ra             = float(words[3]) * cm
        
        ret            = [ { "type":"drift", "name":name, "ds":ds, \
                             "aperture_x":Ra, "aperture_y":Ra } ]
        counts["Ndr"] += 1
        counts["at"]  += ds
        return( ret )

    # ------------------------------------------------- #
    # --- [4] convert_to_rfcavity                   --- #
    # ------------------------------------------------- #
    def convert_to_rfcavity( words, counts ):
        
        MHz       = 1.e+6
        cm        = 1.e-2
        amu       = 931.494    # [MeV]
        
        name      = "rf{}".format( (counts["Nrf"]+1) )
        ds        = 0.0   # tempolarily set as 0 to identify other element's position.
        volt      = float(words[2])                         # volt :    [MV]
        phase     = float(words[3])                         #           [deg]
        harmonics =   int(words[4])                         # harmonics
        Ra        =   int(words[5]) * cm                    # R-cavity  [cm]
        
        ret       = [ { "type":"rfcavity", "name":name, "ds":ds, \
                        "volt":volt, "phase":phase, "harmonics":harmonics, \
                        "aperture_x":Ra, "aperture_y":Ra,  } ]
        counts["Nrf"] += 1
        counts["at"]  += ds
        return( ret )

    # ------------------------------------------------- #
    # --- [5] analyze each line                     --- #
    # ------------------------------------------------- #
    seq    = []
    counts = { "at":0.0, "N":0, "Nqm":0, "Nrf":0, "Ndr":0, }
    for ik,line in enumerate(lines):
        line_ = re.sub( r"#.*", "", line ).strip()
        words = ( line_.split() )
        if ( not( len( words ) == 0 ) ):
            counts["N"]   += 1
            
            if   ( words[1].lower()  == "quad" ):
                seq += convert_to_quad ( words, counts )

            elif ( words[1].lower()  == "drift" ):
                seq += convert_to_drift( words, counts )
                
            elif ( words[1].lower()  == "rfgap" ):
                seq += convert_to_rfcavity ( words, counts )
            else:
                sys.exit( "[ERROR] undefined keyword :: {} ".format( words[1] ) )

    L_tot     = counts["at"]
    Nelements = counts["N"]
    print( f" -- all of the {Nelements} elements were loaded... " )
    print( f" --    total length of the beam line == {L_tot:.8} " )
    print()

    # ------------------------------------------------- #
    # --- [6] save as a json file                   --- #
    # ------------------------------------------------- #
    elements = { el["name"]:el for el in seq }
    sequence = list( elements.keys() )
    beamline = { "sequence":sequence, "elements":elements }
    with open( trackBLFile, "w" ) as f:
        json5.dump( beamline, f, indent=2 )
        print( "[translate__track2impactx.py] output :: {}".format( trackBLFile ) )
    return( beamline )
        
    

# ========================================================= #
# ===  translate__impactxElements.py                    === #
# ========================================================= #

def translate__impactxElements( paramsFile   ="dat/parameters.json", \
                                trackBLFile  ="dat/beamline_track.json", \
                                impactxBLFile="dat/beamline_impactx.json", \
                                phaseFile    ="dat/rfphase.csv" ):

    # ------------------------------------------------- #
    # --- [1] load files                            --- #
    # ------------------------------------------------- #
    with open( paramsFile, "r" ) as f:
        params   = json5.load( f )
    with open( trackBLFile, "r" ) as f:
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
        omega       = params["beam.freq"] * params["beam.harmonics"] * 2.0 * np.pi
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
        freq   = params["beam.freq"] * params["beam.harmonics"]
        escale = element["volt"] / ds / Em0
        phase  = phase_df["phi_c"].loc[ element["name"] ]
        ret    = { "type":element["type"], "name":element["name"], "ds":ds, "escale":escale, \
                   "freq":freq, "phase":phase, \
                   "aperture_x":element["aperture_x"], "aperture_y":element["aperture_y"] } 
        return( ret )
    
    # ------------------------------------------------- #
    # --- [2] call converter                        --- #
    # ------------------------------------------------- #
    rfgap_mode = False
    phase_df  = guess__RFcavityPhase( elements=elements, params=params, phaseFile=phaseFile )
    elements_ = {}
    for key in sequence:
        if   ( elements[key]["type"].lower() in [ "rfcavity" ] ):
            ret            = convert__rfcavity( elements[key], params, phase_df )
            elements_[key] = { **ret, **params["translate.cavity.options" ] }
            if ( rfgap_mode ):
                print( "hi" )
                sys.exit()
                ret            = convert__rfgap( elements[key], params, phase_df )
                elements_[key] = { **ret }
        elif ( elements[key]["type"].lower() in [ "rfgap" ] ):
            ret            = convert__rfgap( elements[key], params, phase_df )
            elements_[key] = { **ret, **params["translate.cavity.options" ] }
        elif ( elements[key]["type"].lower() in [ "quadrupole" ] ):
            elements_[key] = { **elements[key], **params["translate.quad.options" ] }
        elif ( elements[key]["type"].lower() in [ "drift" ] ):
            elements_[key] = { **elements[key], **params["translate.drift.options"] }

    # ------------------------------------------------- #
    # --- [3] save and return                       --- #
    # ------------------------------------------------- #
    beamline["elements"] = elements_
    with open( impactxBLFile, "w" ) as f:
        json5.dump( beamline , f, indent=2 )
        print( "[translate__track2impactx.py] output :: {}".format( impactxBLFile ) )
    return( beamline )


# ========================================================= #
# ===  convert_to_rfgap                                 === #
# ========================================================= #
def convert__rfgap( element, params, phase_df ):

    amu    = 931.494

    # ------------------------------------------------- #
    # --- [1] rfgap model of the trace3D code       --- #
    # ------------------------------------------------- #
    def rfgap( Vg     = 1.0,       # [MV]
               phi    = -45.0,     # [deg]   # for particle ??
               Ek     = 0.0,       # [MeV]
               mass   = 931.494,   # [MeV]
               charge = 1.0,       # [C/e]
               freq   = 146.0e6 ): # [Hz]
        
        cv      = 2.9979e8         # (m/s)
        qa      = abs( charge )    # (C)
        
        # ------------------------------------------------- #
        # --- [1] calculation                           --- #
        # ------------------------------------------------- #
        phis    =  phi/180.0*np.pi
        lamb    =  cv / freq
        Wi      =  Ek
        dW      =  qa * Vg * np.cos(phis)
        Wm      =  Wi + 0.5*dW
        Wf      =  Wi +     dW
        Weff    =  qa * Vg * np.sin(phis)
        gamma_i = 1.0 + Wi/mass
        gamma_m = 1.0 + Wm/mass
        gamma_f = 1.0 + Wf/mass
        bg_i    = np.sqrt( gamma_i**2 - 1.0 )
        bg_m    = np.sqrt( gamma_m**2 - 1.0 )
        bg_f    = np.sqrt( gamma_f**2 - 1.0 )
        beta_m  = bg_m / gamma_m
        kx      = (-1.0)*( np.pi*Weff ) / ( mass *   bg_m**2 * lamb ) 
        ky      = (-1.0)*( np.pi*Weff ) / ( mass *   bg_m**2 * lamb )
        kz      = (+2.0)*( np.pi*Weff ) / ( mass * beta_m**2 * lamb )
        p0c     = np.sqrt( Ek**2 + 2.0*Ek*mass )  # (MeV)
        
        # ------------------------------------------------- #
        # --- [2] r-matrix                              --- #
        # ------------------------------------------------- #
        #  -- trace3D notation --  #
        # rmdiag  = bg_i / bg_f
        # rm11    =   1.0
        # rm22    = rmdiag
        # rm33    =   1.0
        # rm44    = rmdiag
        # rm55    =   1.0
        # rm66    = rmdiag
        # rm21    = kx / bg_f
        # rm43    = ky / bg_f
        # rm65    = kz / bg_f
        # kick6   = 0.0
        
        #  -- my notation ( for [T, PT] ) --  #
        rmat_     = np.zeros( (7,7) )
        rmat_[1,1] =   1.0
        rmat_[2,2] = bg_i / bg_f
        rmat_[3,3] =   1.0
        rmat_[4,4] = bg_i / bg_f
        rmat_[5,5] =   1.0
        rmat_[6,6] = gamma_i / gamma_f    #  PT = dE/(p0 c)  !=  dp/p0
        rmat_[2,1] = kx / bg_f
        rmat_[4,3] = ky / bg_f
        rmat_[6,5] = kz / ( gamma_f )
        # kick6     = dW / p0c
        rmat       = np.copy( rmat_[1:,1:] )
        
        # ------------------------------------------------- #
        # --- [3] return                                --- #
        # ------------------------------------------------- #
        # ret     = { "rm11":rm11, "rm21":rm21, "rm22":rm22, \
            #             "rm33":rm33, "rm43":rm43, "rm44":rm44, \
            #             "rm55":rm55, "rm65":rm65, "rm66":rm66, \
            #             "kick6":kick6, \
            #            }
        return( rmat )

    # ------------------------------------------------- #
    # --- [2] set values for LinearMap              --- #
    # ------------------------------------------------- #
    name   = element["name"].replace( "rf", "gap" )
    Vg     = element["volt"]
    phi    = phase_df["phi_c"].loc[ element["name"] ]
    Ek     = phase_df["Ek"]
    mass   = params["beam.mass.amu"] * amu
    charge = params["beam.charge"]
    freq   = params["beam.freq"] * params["beam.harmonics"]
    Rmat   = rfgap( Vg=Vg, phi=phi, Ek=Ek, mass=mass, charge=charge, freq=freq )
    ret    = { "type":"rfgap", "name":name, "ds":0.0, "R":,Rmat  }
    return( ret )

    
# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    translate__track2impactx()
