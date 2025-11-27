import os, sys, json5, re
import numpy          as np
import pandas         as pd

# ========================================================= #
# ===  extract__trackv38_beamline.py                    === #
# ========================================================= #

def extract__trackv38_beamline( trackFile="track/sclinac.dat", \
                                outFile="dat/beamline.json" ):
    
    # ------------------------------------------------- #
    # --- [1] read track file                       --- #
    # ------------------------------------------------- #
    with open( trackFile, "r" ) as f:
        lines  = f.readlines()
        
    # ------------------------------------------------- #
    # --- [2] analyze each line                     --- #
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
                seq += convert_to_rfcavity( words, counts )
            
            else:
                sys.exit( "[ERROR] undefined keyword :: {} ".format( words[1] ) )

    L_tot     = counts["at"]
    Nelements = counts["N"]
    print( f" -- all of the {Nelements} elements were loaded... " )
    print( f" --    total length of the beam line == {L_tot:.8} " )
    print()

    # ------------------------------------------------- #
    # --- [3] save as a json file                   --- #
    # ------------------------------------------------- #
    elements = { el["name"]:el for el in seq }
    sequence = list( elements.keys() )
    beamline = { "sequence":sequence, "elements":elements }
    with open( outFile, "w" ) as f:
        json5.dump( beamline, f, indent=2 )
    return( seq )
        
    
    
# ========================================================= #
# ===  convert_to_quad                                  === #
# ========================================================= #
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


# ========================================================= #
# ===  convert_to_drift                                 === #
# ========================================================= #
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


# ========================================================= #
# ===  convert_to_rfcavity                              === #
# ========================================================= #
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
    extract__trackv38_beamline()


    






# # ------------------------------------------------- #
#     # --- [3] modify rfcavity thickness             --- #
#     # ------------------------------------------------- #
#     if ( params["translate.rf.thickness"] ):
#         at   = 0.0
#         Lcav = params["translate.rf.thickness"]
        
#         # ------------------------------------------------- #
#         # --- [3-1] modify length   - DR - RF - DR -    --- #
#         # ------------------------------------------------- #
#         for ik in range( len(seq) ):
            
#             if ( seq[ik]["type"].lower() == "rfcavity" ):
#                 seq[ik]["L"] = Lcav
                
#                 # -- check previous drift &  L_dr = L_dr - L_cav/2
#                 if ( ik != 0 ):
#                     if ( seq[ik-1]["type"].lower()=="drift" ):
#                         seq[ik-1]["L"] = seq[ik-1]["L"] - 0.5*Lcav
#                     else:
#                         print( "[CAUTION] {0} is rfcavity, but {1} is not drift... [CAUTION]"\
#                                .format( seq[ik]["name"], seq[ik-1]["tag"] ) )
#                         sys.exit()
                        
#                 # -- check next drift     &  L_dr = L_dr - L_cav/2
#                 if ( ik != len(seq) ):
#                     if ( seq[ik+1]["type"].lower()=="drift" ):
#                         seq[ik+1]["L"] = seq[ik+1]["L"] - 0.5*Lcav
#                     else:
#                         print( "[CAUTION] {0} is rfcavity, but {1} is not drift... [CAUTION]"\
#                                .format( seq[ik]["tag"], seq[ik+1]["tag"] ) )
#                         sys.exit()

#         # ------------------------------------------------- #
#         # --- [3-2] sum up "at" position again          --- #
#         # ------------------------------------------------- #
#         for ik,elem in enumerate( seq ):
#             elem["at"]  = at
#             at         += elem["L"]
            
#     # ------------------------------------------------- #
#     # --- [4] convert into mad-x sequence           --- #
#     # ------------------------------------------------- #
#     contents  = "import impactx" + "\n\n"
#     contents += "ns = {}\n".format( params["translate.nslice"] )
#     base_f    = "{0:<8} = impactx.elements."
#     if ( params["translate.trackmode"].lower() in ["nonlinear"] ):
#         drift_f   = base_f + 'ExactDrift( name="{0}", ds={1:.8}, aperture_x={2:.8}, aperture_y={2:.8}, nslice=ns )\n'
#         quadr_f   = base_f + 'ExactQuad ( name="{0}", ds={1:.8}, unit=1, k={2:.8}, aperture_x={3:.8}, aperture_y={3:.8}, nslice=ns )\n'
#         rfcav_f   = base_f + 'RFCavity  ( name="{0}", ds={1:.8}, escale={2:.8}, freq={3:.8}, phase={4:.8}, cos_coefficients={5}, sin_coefficients={6}, aperture_x={7:.8}, aperture_y={7:.8}, nslice=ns )\n'
#     else:
#         drift_f   = base_f + 'Drift   ( name="{0}", ds={1:.8}, aperture_x={2:.8}, aperture_y={2:.8}, nslice=ns )\n'
#         quadr_f   = base_f + 'Quad    ( name="{0}", ds={1:.8}, k={2:.8}, aperture_x={3:.8}, aperture_y={3:.8}, nslice=ns )\n'
#         rfcav_f   = base_f + 'RFCavity( name="{0}", ds={1:.8}, escale={2:.8}, freq={3:.8}, phase={4:.8}, cos_coefficients={5}, sin_coefficients={6}, aperture_x={7:.8}, aperture_y={7:.8}, nslice=ns )\n'

#     if ( params["translate.add_monitor"] ):
#         contents  += ( base_f + 'BeamMonitor( "{0}", backend="h5")\n' ).format( "bpm" )
    
#     for ik,elem in enumerate(seq):
        
#         if   ( elem["type"].lower() == "drift"      ):
#             keys      = [ "tag", "L", "aperture" ]
#             contents += drift_f.format( *( [ elem[key] for key in keys ] ) )
            
#         elif ( elem["type"].lower() == "quadrupole" ):
#             keys      = [ "tag", "L", "K1", "aperture" ]
#             contents += quadr_f.format( *( [ elem[key] for key in keys ] ) )
            
#         elif ( elem["type"].lower() == "rfcavity"   ):
#             keys      = [ "tag", "L", "escale", "freq", "phase", \
#                           "cos_coeff", "sin_coeff", "aperture"]
#             contents += rfcav_f.format( *( [ elem[key] for key in keys ] ) )
            
#         else:
#             print( "[extract__trackv38_beamline.py] unknown keywords :: {} ".format( elem["type"] ) )
#             sys.exit()

#     # ------------------------------------------------- #
#     # --- [5] beam line definition                  --- #
#     # ------------------------------------------------- #
#     if ( params["translate.add_monitor"] ):
#         elements = ["bpm"]
#         for elem in seq:
#             if ( elem["type"].lower() in [ "quadrupole", "rfcavity" ] ):
#                 elements += [ elem["tag"], "bpm" ]
#             else:
#                 elements += [ elem["tag"] ]
#     else:
#         elements = [ elem["tag"] for elem in seq ]
        
#     contents += "beamline = [ " + ",".join( elements ) + " ]\n"

#     # ------------------------------------------------- #
#     # --- [6] write in a file                       --- #
#     # ------------------------------------------------- #
#     with open( params["file.sequence"], "w" ) as f:
#         f.write( contents )
#     return()
