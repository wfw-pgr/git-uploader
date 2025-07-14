import os, sys
import pandas as pd
import numpy  as np

# ========================================================= #
# ===  twiss__fromTrackline.py                          === #
# ========================================================= #

def twiss__fromTrackline( df=None, axis="x", digit=6 ):
    """
    evaluate twiss parameters from trackline results....
    """
    
    # ------------------------------------------------- #
    # --- [1] Arguments                             --- #
    # ------------------------------------------------- #
    if ( df is None ): sys.exit( "[twiss__fromTrackline.py] df == ???" )
    if ( axis == "x" ):
        xkey, pkey = "X", "PX"
    elif ( axis == "y" ):
        xkey, pkey = "Y", "PY"
    else:
        sys.exit( "undefined axis :: {}".format( axis ) )
        
    # ------------------------------------------------- #
    # --- [2] make position list                    --- #
    # ------------------------------------------------- #
    df["S"] = df["S"].apply( lambda x: significant_digit( x, digit=digit ) )
    sarr    = sorted( list( set( df["S"] ) ) )
    
    # ------------------------------------------------- #
    # --- [2] evaluation                            --- #
    # ------------------------------------------------- #
    stack   = []
    for ik,sv in enumerate( sarr ):
        sgroup  = df[ df["S"] == sv ]
        xp      = sgroup["X"] .values
        px      = sgroup["PX"].values
        yp      = sgroup["Y"] .values
        py      = sgroup["PY"].values
        xpxcov  = np.cov( xp,px )
        xp2avg  = xpxcov[0,0]
        px2avg  = xpxcov[1,1]
        xpxavg  = xpxcov[0,1]
        ypycov  = np.cov( yp,py )
        yp2avg  = ypycov[0,0]
        py2avg  = ypycov[1,1]
        ypyavg  = ypycov[0,1]
        emit_x  = np.sqrt( xp2avg * px2avg - xpxavg**2 )
        emit_y  = np.sqrt( yp2avg * py2avg - ypyavg**2 )
        beta_x  =          xp2avg / emit_x
        beta_y  =          yp2avg / emit_y
        gamma_x =          px2avg / emit_x
        gamma_y =          py2avg / emit_y
        alpha_x = (-1.0) * xpxavg / emit_x
        alpha_y = (-1.0) * ypyavg / emit_y
        stack += [ np.array( [ sv,\
                               emit_x, beta_x, alpha_x, gamma_x,\
                               emit_y, beta_y, alpha_y, gamma_y ] ) [np.newaxis,:] ]
    stack   = np.concatenate( stack, axis=0 )
    columns = [ "S", \
                "emit_x", "beta_x", "alpha_x", "gamma_x", \
                "emit_y", "beta_y", "alpha_y", "gamma_y" ]
    ret     = pd.DataFrame( stack, columns=columns )
    return( ret )


# ========================================================= #
# ===  significant-digit                                === #
# ========================================================= #
def significant_digit( x, digit=8 ):
    "return significant digit of x"
    if   ( pd.isna(x) ):
        return x
    elif ( x == 0     ):
        return 0
    else:
        return round( x, digit-int( np.floor(np.log10(abs(x)))) - 1 )

# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    
    inpFile = "madx/out/trackline.h5"
    outFile = "dat/twiss__fromTrackLine.h5"
    df      = pd.read_hdf( inpFile )
    twiss   = twiss__fromTrackline( df=df )
    twiss.to_hdf( outFile, key="data" )
    print( " output :: {}".format( outFile ) )
