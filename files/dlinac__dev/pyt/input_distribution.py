import numpy as np
import matplotlib.pyplot as plt

def compute_emittances( Ek0, Em0, e995_pi_mm,
                        multiply_pi=True,
                        e995_to_1sigma = 1.0/2.807,
                        mm = 1.0e-3, mrad = 1.0e-3):
    """
    Convert user inputs -> normalized (1sigma) and geometric emittances (SI).
    - Ek0: kinetic energy [MeV]
    - Em0: rest mass [MeV]
    - e995_pi_mm: numeric input (interpreted as either N [mm mrad] or N*pi [mm mrad])
    - multiply_pi: whether to multiply e995_pi_mm by pi (True if variable stored as '20' meaning 20*pi)
    - returns: eps_norm_1sigma [m rad], eps_geom [m rad]
    """
    # normalized 99.5% -> normalized 1σ
    e995 = e995_pi_mm * (np.pi if multiply_pi else 1.0) * mm * mrad     # [m·rad] (99.5%)
    eps_norm_1sigma = e995 * e995_to_1sigma                              # convert 99.5% -> 1σ

    # relativistic conversion: geometric = normalized / (beta_rel * gamma_rel)
    gamma_rel = 1.0 + Ek0/Em0
    beta_rel = np.sqrt(1.0 - gamma_rel**(-2.0))
    eps_geom = eps_norm_1sigma / (beta_rel * gamma_rel)

    return eps_norm_1sigma, eps_geom, beta_rel, gamma_rel



def twiss_ellipse(alpha, beta, eps, npoints=360):
    """
    Parametric points (q, p) of the phase-space ellipse:
      gamma q^2 + 2 alpha q p + beta p^2 = eps
    Parametrization:
      q  = sqrt(eps * beta) * cos(theta) * r
      p  = -sqrt(eps / beta) * ( alpha*cos(theta) + sin(theta) ) * r
    where r=1 for boundary; for waterbag sampling use r in [0,1]**0.5
    returns q_array, p_array for boundary (r=1)
    """
    if eps <= 0 or beta <= 0:
        raise ValueError("eps and beta must be positive")
    gamma_twiss = (1 + alpha**2) / beta
    th = np.linspace(0, 2*np.pi, npoints)
    q = np.sqrt(eps * beta) * np.cos(th)
    p = -np.sqrt(eps / beta) * (alpha * np.cos(th) + np.sin(th))
    return q, p



def sample_waterbag(alpha, beta, eps, npoints=2000):
    """
    Uniform samples inside ellipse (waterbag-like).
    r = sqrt(u) scaling ensures uniform area.
    """
    th = np.random.rand(npoints) * 2*np.pi
    r = np.sqrt(np.random.rand(npoints))
    qb, pb = twiss_ellipse(alpha, beta, eps, npoints=len(th))
    # qb,pb correspond to r=1 parameterized by th in order; we can scale by r
    q = r * np.sqrt(eps * beta) * np.cos(th)
    p = r * (-np.sqrt(eps / beta) * (alpha * np.cos(th) + np.sin(th)))
    return q, p



def plot_beam_envelopes(Ek0, Em0, e995_pi_mm,
                        alpha_xyt, beta_xyt,
                        multiply_pi=True,
                        long_emittance_scale=None,
                        npoints_ellipse=360,
                        show_samples=False,
                        sample_n=4000):
    """
    Draw envelopes for x-x', y-y', t-delta planes.
    - alpha_xyt, beta_xyt are arrays of length 3 (x,y,t)
    - long_emittance_scale: optional multiplier to eps_geom for longitudinal plane
      (if None, use same eps_geom; you can e.g. pass 1.2/15)
    - show_samples: overlay samples uniform in ellipse (waterbag)
    """
    # compute emittances
    eps_norm_1sigma, eps_geom, beta_rel, gamma_rel = compute_emittances(Ek0, Em0, e995_pi_mm, multiply_pi=multiply_pi)
    # per-plane geometric emittances (use same for x,y; allow override for t)
    eps_x = eps_geom
    eps_y = eps_geom
    if long_emittance_scale is None:
        eps_t = eps_geom
    else:
        eps_t = eps_geom * long_emittance_scale

    eps_xyt = np.array([eps_x, eps_y, eps_t])

    planes = ['x (m) vs x\' (rad)', 'y (m) vs y\' (rad)', 'z (m) vs δ (unitless)']
    fig, axs = plt.subplots(1,3, figsize=(15,5))
    for i, ax in enumerate(axs):
        alpha = alpha_xyt[i]
        beta = beta_xyt[i]
        eps = eps_xyt[i]
        q, p = twiss_ellipse(alpha, beta, eps, npoints=npoints_ellipse)
        # choose unit conversion for display:
        if i in [0,1]:
            # show x in mm, p in mrad
            ax.plot(q*1e3, p*1e3, '-', lw=1.5)
            if show_samples:
                qs, ps = sample_waterbag(alpha, beta, eps, npoints=sample_n)
                ax.scatter(qs*1e3, ps*1e3, s=2, alpha=0.2)
            ax.set_xlabel(f"{['x','y'][i]} [mm]")
            ax.set_ylabel(f"{['x\'','y\''][i]} [mrad]")
        else:
            # longitudinal: z in mm, delta in percent
            ax.plot(q*1e3, p*100.0, '-', lw=1.5)   # p is unitless delta -> %
            if show_samples:
                qs, ps = sample_waterbag(alpha, beta, eps, npoints=sample_n)
                ax.scatter(qs*1e3, ps*100.0, s=2, alpha=0.2)
            ax.set_xlabel("z [mm]")
            ax.set_ylabel("δ = ΔE/E [%]")
        ax.grid(True)
        ax.set_title(planes[i])

    fig.suptitle(f"Beam envelopes (eps_geom={eps_geom:.2e} m·rad, eps_norm_1σ={eps_norm_1sigma:.2e} m·rad, β_rel={beta_rel:.3f})")
    plt.tight_layout(rect=[0,0,1,0.95])
    return fig, axs



# ---------------------------
# Example usage with your inputs
# ---------------------------
if __name__ == "__main__":
    Ek0        = 40.0                                  # [MeV]
    amu        = 931.494
    Em0        = 2.014 * amu                           # [MeV]
    e995_pi_mm = 20.0                                  # value from user
    alpha_xyt  = np.array( [ 0.0, 0.0, 0.0 ] )
    beta_xyt   = np.array( [ 8.0, 4.0, 0.2 ] )         # [m]
    # if e995_pi_mm is actually "20*pi mm mrad", set multiply_pi=True; else False
    fig, axs = plot_beam_envelopes(Ek0, Em0, e995_pi_mm,
                                   alpha_xyt, beta_xyt,
                                   multiply_pi=True,          # choose according to your convention
                                   long_emittance_scale=1.2/15.0,  # if you want same tweak as earlier
                                   show_samples=True,
                                   sample_n=2000)
    plt.show()
