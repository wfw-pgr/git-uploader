import os, sys
import numpy  as np
import pandas as pd

# ========================================================= #
# ===  translate__track2madx.py                         === #
# ========================================================= #

def translate__track2madx( seq_tag  = "MidBeta", seqFile="madx/1a-deuteron.seq", \
                           trackFile= "track/sclinac.dat", energyFile="track/beam.out" ):
    
    cm      = 1.e-2
    MeV     = 1.e6
    gauss   = 1.e-4           # [T]
    freq_0  = 36.5            # [MHz]
    cv      = 2.99792458e8    # [m/s]
    qe      = 1.60217663e-19  # [C]
    Nu      = 2.0
    um      = 931.494         # [MeV]
    mc2     = 2.0141018 * um  # [MeV]
    LagSign = +1.0
    
    # ------------------------------------------------- #
    # --- [1] read track file                       --- #
    # ------------------------------------------------- #
    with open( trackFile, "r" ) as f:
        lines = f.readlines()
    with open( energyFile, "r" ) as f:
        energy = pd.read_csv( f, header=0, sep=r"\s+" )
        
    # ------------------------------------------------- #
    # --- [2] analyze each line                     --- #
    # ------------------------------------------------- #
    seq   = []
    qmnum = 0
    rfnum = 0
    elnum = 0
    at    = 0.0
    for ik,line in enumerate(lines):
        words = ( line.split() )
        if ( not( len( words ) == 0 ) ):
            elnum += 1
            if   ( words[1]  == "quad" ):
                qmnum += 1
                Ek     = energy["Energy[MeV/u]"][elnum] * Nu  #  -- [MeV]
                pc     = np.sqrt( Ek**2 + 2.0*Ek*mc2 )        #  -- [MeV] = c*p
                BRho   = pc * MeV / cv                        #  -- [Tm]  = p/q = pc*qe/(cv*qe)
                gradB  = ( float(words[2])*gauss ) / ( float(words[5])*cm )  # -- [T/m]
                K1     = gradB / BRho                         #  -- [1/m2]
                L      = float(words[4]) * cm
                seq   += [ { "type":"quadrupole", "tag": f"qm{qmnum}",
                             "K1":K1, "L":L, "at":at, "Ek":Ek } ]
                at    += L
            elif ( words[1]  == "drift" ):
                L      = float(words[2]) * cm
                at    += L
            elif ( words[1]  == "rfgap" ):
                rfnum += 1
                L      = 0.0 * cm
                volt   = float(words[2])
                lag    = LagSign * float(words[3]) / 360.0
                harmon =   int(words[4])
                freq   = freq_0
                at    += L
                seq   += [ { "type":"RFcavity", "tag":f"rf{rfnum}", "L":0.0, "volt":volt, \
                             "lag":lag, "freq":freq, "harmon":harmon, "at":at } ]
            else:
                sys.exit( "[ERROR] undefined keyword :: {} ".format( words[1] ) )
    L_tot  = at
    print()
    print( f" -- all of the {elnum} elements were loaded...   -- " )
    print( f" --    total length of the beam line == {L_tot:.8} -- " )
    print()
                
    # ------------------------------------------------- #
    # --- [3] convert into mad-x sequence           --- #
    # ------------------------------------------------- #
    contents  = ""
    contents += "{0}: sequence, L={1:.8}, refer=entry;\n".format( seq_tag, L_tot )
    for ik,elem in enumerate(seq):
        if   ( elem["type"].lower() == "quadrupole" ):
            contents += "  {0}: quadrupole, L={1:.8}, K1={2:.8}, at={3:.8};\n"\
                .format( elem["tag"], elem["L"], elem["K1"], elem["at"] )
        elif ( elem["type"].lower() == "rfcavity"   ):
            contents += "  {0}: RFCavity, L={1:.8}, volt={2:.8}, lag={3:.8}, freq={4:.4}, harmon={5}, at={6:.8};\n"\
                .format( elem["tag"], elem["L"], elem["volt"], elem["lag"], elem["freq"], elem["harmon"], elem["at"] )
    contents += "endsequence;"
    with open( seqFile, "w" ) as f:
        f.write( contents )

            
# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    translate__track2madx()

