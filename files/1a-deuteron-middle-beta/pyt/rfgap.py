import sys
import numpy as np
import pandas as pd

# ========================================================= #
# ===  rfgap.py                                         === #
# ========================================================= #

def rfgap( Vg     = 1.0,       # [MV]
           phi    = -45.0,     # [deg]
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
    # ------------------------------------------------- #
    # --- [2] r-matrix                              --- #
    # ------------------------------------------------- #
    rmdiag  = bg_i / bg_f
    rm11    =   1.0
    rm22    = rmdiag
    rm33    =   1.0
    rm44    = rmdiag
    rm55    =   1.0
    rm66    = rmdiag
    rm21    =   kx / bg_f
    rm43    =   ky / bg_f
    rm65    =   kz / bg_f
    
    rm21    = rm21 / 1.0
    rm43    = rm43 / 1.0
    rm65    = rm65 / 1.0
    # rm65    = rm65 + ( 2.0*np.pi*freq * Vg*np.cos(phi) / ( mass * bg_m * c )
    # kick6   =   dW / ( mass * bg_m )
    kick6   = 0.0
    
    # ------------------------------------------------- #
    # --- [3] return                                --- #
    # ------------------------------------------------- #
    ret     = { "rm11":rm11, "rm21":rm21, "rm22":rm22, \
                "rm33":rm33, "rm43":rm43, "rm44":rm44, \
                "rm55":rm55, "rm65":rm65, "rm66":rm66, \
                "rmdiag":rmdiag, "kick6":kick6, \
               }
    return( ret )


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):

    Vg     = 1.0
    phi    = -45.0
    mass   = 2.014 * 931.494 #  [MeV]
    charge = 1.0
    freq   = 146.0e6         #  [Hz]
    Ek     = 40.0            #  [MeV]
    
    ret    = rfgap( Vg=Vg, phi=phi, Ek=Ek, mass=mass, charge=charge, freq=freq )
    print( ret )
    
