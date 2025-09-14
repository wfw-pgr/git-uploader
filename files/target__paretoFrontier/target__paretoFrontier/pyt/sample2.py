import numpy as np
import pandas as pd
import scipy.special as spc
from scipy.stats import norm

def calculate__risk_return(
    sigma_b=1.0,
    csvFile="dat/risk_return.csv",
    Yreq_A0 = 0.90,
    alpha = 0.95,
    use_montecarlo = False,
    nmc = 20000,
    random_state = 0
):
    
    # ------------------------------------------------- #
    # --- [1] load data                             --- #
    # ------------------------------------------------- #
    coefs   = pd.read_csv( "dat/fit_coefs.csv" )
    A0      = coefs["a0"].to_numpy()
    wy      = coefs["a2"].to_numpy()

    # ------------------------------------------------- #
    # --- [2] calculate E[Y], V[Y]                  --- #
    # ------------------------------------------------- #
    r_sigma = sigma_b / wy
    EY      = A0 / np.sqrt( 1.0 + r_sigma**2 )
    EY2     = A0**2 / np.sqrt( 1.0 + 2.0 * r_sigma**2 )
    VY      = EY2 - EY**2
    sigmaY  = np.sqrt( np.maximum(VY, 0.0) )

    # ------------------------------------------------- #
    # --- [3] miss probability (original)           --- #
    # ------------------------------------------------- #
    # keep original "beam" based Pmiss (your existing formula)
    t_beam        = wy / sigma_b * np.sqrt( np.log( 1.0/Yreq_A0 ) )
    Pmiss_beam    = spc.erfc( t_beam )   # keep existing name/behavior

    # ------------------------------------------------- #
    # --- [4] define threshold Yc                   --- #
    # ------------------------------------------------- #
    Yc = Yreq_A0 * A0

    # ------------------------------------------------- #
    # --- [5] normal-approx quantities (vectorized)  -#
    # ------------------------------------------------- #
    eps = 1e-16
    # shortage probability under normal approx: P(Y < Yc)
    with np.errstate(divide='ignore', invalid='ignore'):
        z_t = (Yc - EY) / np.where(sigmaY > 0, sigmaY, np.nan)
        p_loss = norm.cdf(z_t)                      # P(Y<Yc)
        p_loss = np.where(np.isnan(p_loss), 0.0, p_loss)

    # conditional E[Y | Y < Yc] under normal
    phi_t = norm.pdf(z_t)
    Phi_t = p_loss.copy()
    Phi_safe = np.maximum(Phi_t, eps)

    EY_cond = np.empty_like(EY)
    # degenerate sigma=0 case
    deg = sigmaY < 1e-12
    EY_cond[deg] = EY[deg]   # point mass; if EY < Yc then L=Yc-EY else no loss
    nondeg = ~deg
    EY_cond[nondeg] = EY[nondeg] - sigmaY[nondeg] * (phi_t[nondeg] / Phi_safe[nondeg])

    # E[L | L>0] and E[L]
    E_L_given_loss = np.maximum(0.0, Yc - EY_cond)
    E_L = p_loss * E_L_given_loss

    # ------------------------------------------------- #
    # --- [6] VaR and CVaR (parametric normal approx) - #
    # ------------------------------------------------- #
    p_tail = 1.0 - alpha
    if not (0.0 < alpha < 1.0):
        raise ValueError("alpha must be in (0,1)")

    z_p = norm.ppf(p_tail)   # quantile for Y: lower p_tail quantile
    q_p = EY + sigmaY * z_p  # q_{p_tail}(Y)

    # VaR_alpha(L) = max(0, Yc - q_p)
    VaR_param = np.maximum(0.0, Yc - q_p)

    # CVaR_alpha(L) = max(0, Yc - E[Y | Y <= q_p]) with normal formula
    phi_zp = norm.pdf(z_p)
    # E[Y | Y <= q_p] = EY - sigma * phi(z_p)/p_tail
    E_trunc = np.empty_like(EY)
    E_trunc[deg] = EY[deg]
    E_trunc[nondeg] = EY[nondeg] - sigmaY[nondeg] * (phi_zp / (p_tail + eps))
    CVaR_param = np.maximum(0.0, Yc - E_trunc)
    # if shortage probability p_loss < p_tail then CVaR_alpha(L) = 0 by definition (no shortages in worst p_tail)
    CVaR_param = np.where(p_loss < p_tail, 0.0, CVaR_param)


    # ------------------------------------------------- #
    # --- [8] assemble dataframe and save            --- #
    # ------------------------------------------------- #
    df = pd.DataFrame({
        "A0": A0,
        "wy": wy,
        "EY": EY,
        "EY2": EY2,
        "VY": VY,
        "sigmaY": sigmaY,
        "Yc": Yc,
        "Pmiss_beam": Pmiss_beam,    # your original metric
        "P_loss_norm": p_loss,      # P(Y < Yc) from normal approx
        "E[L|L>0]": E_L_given_loss,
        "E[L]": E_L,
        "VaR_param": VaR_param,
        "CVaR_param": CVaR_param,
        "alpha": alpha,
        "sigma_b": sigma_b
    })

    df.to_csv(csvFile, index=False)
    print("[analyze.py] output :: {} (alpha={:.3f}, use_montecarlo={})".format(csvFile, alpha, use_montecarlo))
    return df


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    calculate__risk_return()
    
