import numpy as np
import pandas as pd
from scipy import special as spsp
from scipy.stats import norm

def calculate__risk_return( sigma_b=1.5, csvFile="dat/risk_return.csv",
                            Yreq_A0=0.90, alpha=0.99, use_montecarlo=False, nmc=20000, random_state=0 ):
    # --- [1] load data
    coefs   = pd.read_csv( "dat/fit_coefs.csv" )
    A0      = coefs["a0"].to_numpy()
    wy      = coefs["a2"].to_numpy()

    # --- [2] calculate E[Y], V[Y]
    r_sigma = sigma_b / wy
    EY      = A0 / np.sqrt( 1.0 + r_sigma**2 )
    EY2     = A0**2 / np.sqrt( 1.0 + 2.0 * r_sigma**2 )
    VY      = EY2 - EY**2
    sigmaY  = np.sqrt( np.maximum(VY, 0.0) )

    # --- [3] miss probability (既存)
    Yreq_A0_val = Yreq_A0   # fraction of A0
    t_beam  = wy / sigma_b * np.sqrt( np.log( 1.0/Yreq_A0_val ) )
    Pmiss   = spsp.erfc( t_beam )
    # ------------------------------------------------
    # --- [4] define threshold Yc (required production)
    Yc = Yreq_A0_val * A0   # shape: same as A0

    # --- [5] compute VaR and CVaR for loss L = max(0, Yc - Y)
    p = 1.0 - alpha   # tail probability, e.g. 0.05 for alpha=0.95

    # initialize
    VaR = np.zeros_like(EY)
    CVaR = np.zeros_like(EY)

    # -------------- Option A: parametric normal approximation (fast)
    # Handle degenerate sigmaY==0 separately
    # q_p = mu + sigma * z_p   where z_p = Phi^{-1}(p)
    z_p = norm.ppf( p )   # scalar
    q_p = EY + sigmaY * z_p   # 1D array

    # VaR  (ensure >=0)
    VaR_param = np.maximum(0.0, Yc - q_p)

    # For CVaR: E[Y | Y <= q_p] for normal is mu - sigma * phi(z_p) / p
    # if sigmaY==0, conditional mean is just EY (degenerate)
    phi_zp = norm.pdf(z_p)
    # avoid division by zero if p extremely small
    if p <= 0.0:
        raise ValueError("alpha must be < 1.0")
    E_trunc = np.empty_like(EY)
    small_mask = (sigmaY < 1e-12)
    E_trunc[small_mask] = EY[small_mask]  # degenerate case
    non_mask = ~small_mask
    E_trunc[non_mask] = EY[non_mask] - sigmaY[non_mask] * (phi_zp / p)

    CVaR_param = np.maximum(0.0, Yc - E_trunc)

    # assign
    VaR[:] = VaR_param
    CVaR[:] = CVaR_param

    # -------------- Option B: Monte Carlo (more accurate if Y is non-normal or you have a generative model)
    if use_montecarlo:
        rng = np.random.default_rng(random_state)
        # We'll sample N draws for each distance (vectorized)
        # draws shape: (n_points, nmc)
        mu = EY
        sig = sigmaY
        npoints = len(mu)
        # To save memory, sample in chunks if needed; here simple implementation:
        draws = rng.normal(loc=mu[:,None], scale=sig[:,None], size=(npoints, nmc))
        L = np.maximum(0.0, Yc[:,None] - draws)   # shape (npoints, nmc)
        # VaR_mc: empirical alpha-quantile of L
        k = int(np.ceil(alpha * nmc)) - 1
        sorted_L = np.sort(L, axis=1)   # ascending
        VaR_mc = sorted_L[:, k]         # empirical VaR
        # CVaR_mc: mean of losses >= VaR_mc
        CVaR_mc = np.empty(npoints)
        for i in range(npoints):
            tail = L[i, L[i] >= VaR_mc[i] - 1e-15]   # numerical safeguard
            if tail.size == 0:
                CVaR_mc[i] = 0.0
            else:
                CVaR_mc[i] = tail.mean()
        VaR[:] = VaR_mc
        CVaR[:] = CVaR_mc

    # --- [6] assemble dataframe
    df = pd.DataFrame( { "EY":EY, "EY2":EY2, "VY":VY, "Pmiss":Pmiss,
                         "Yc":Yc, "VaR":VaR, "CVaR":CVaR } )
    df["sigma_b"] = sigma_b
    # df.to_csv( csvFile, index=False )
    # print( "[analyze.py] output :: {} ".format( csvFile ) )
    return df



def display( df ):

    import nk_toolkit.plot.load__config   as lcf
    import nk_toolkit.plot.gplot1D        as gp1

    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [4.5,4.5],
        "figure.pngFile"     : "png/CVaR-EY.png", 
        "figure.position"    : [ 0.16, 0.16, 0.94, 0.94 ],
        "ax1.y.normalize"    : 1.0e0, 
        "ax1.x.range"        : { "auto":False, "min": 0.0, "max":10e-9, "num":11 },
        "ax1.y.range"        : { "auto":False, "min": 0.0, "max":10e-9, "num":11 },
        "ax1.x.label"        : "CVaR",
        "ax1.y.label"        : "E[Y]",
        "ax1.x.minor.nticks" : 1, 
        "plot.marker"        : "o",
        "plot.markersize"    : 3.0,
        "legend.fontsize"    : 9.0, 
    }
    config = { **config, **config_ }
        
    fig    = gp1.gplot1D( config=config )

    sb_list = sorted( list( set( df["sigma_b"] ) ) )
    for ik, sb in enumerate( sb_list ):
        xAxis = df[ df["sigma_b"]==sb ]["CVaR"]
        yAxis = df[ df["sigma_b"]==sb ]["EY"]
        fig.add__plot( xAxis=xAxis, yAxis=yAxis, label="sb={:.1f} mm".format( sb ) )
    fig.set__axis()
    fig.set__legend()
    fig.save__figure()

    

# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):

    sb_list = [ 0.6, 0.8, 1.0, 1.2, 1.4, 1.6 ]

    stack = []
    for ik,sb in enumerate( sb_list ):
        stack += [ calculate__risk_return( sigma_b=sb ) ]
    df = pd.concat( stack, axis=0 )
    display( df )
