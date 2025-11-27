import json5
import os, sys
import numpy as np


# ========================================================= #
# ===  adjust__driftlength.py                           === #
# ========================================================= #
def adjust__driftlength( impactxBLFile = "dat/beamline_impactx.json", Lcav=0.0 ):

    # ------------------------------------------------- #
    # --- [1] load data                             --- #
    # ------------------------------------------------- #
    with open( impactxBLFile, "r" ) as f:
        beamline = json5.load( f )
    sequence = beamline["sequence"]
    elements = beamline["elements"]
    nSeq     = len( sequence )

    # ------------------------------------------------- #
    # --- [2] re-length                             --- #
    # ------------------------------------------------- #
    for ik, seq in enumerate(sequence):
        prev, next = None, None
        if ( ik-1 >= 0    ): prev = sequence[ik-1]
        if ( ik+1 <  nSeq ): next = sequence[ik+1]
        if ( elements[seq]["type"].lower() in [ "rfcavity" ] ):
            if ( prev is not None ):
                if ( elements[prev]["type"] in ["drift"] ):
                    if ( elements[prev]["ds"] > 0.5 * Lcav ):
                        elements[prev]["ds"] -= Lcav*0.5
            if ( next is not None ):
                if ( elements[next]["type"] in ["drift"] ):
                    if ( elements[next]["ds"] > 0.5 * Lcav ):
                        elements[next]["ds"] -= Lcav*0.5
    beamline["elements"] = elements

    # ------------------------------------------------- #
    # --- [3] save and return                       --- #
    # ------------------------------------------------- #
    with open( impactxBLFile, "w" ) as f:
        json5.dump( beamline , f, indent=2 )
        print( "[adjust__driftlength] output :: {}".format( impactxBLFile ) )
    return( beamline )

# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    adjust__driftlength( Lcav=0.0000002 )
