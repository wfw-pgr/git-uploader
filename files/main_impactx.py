import os, sys, json5
import impactx
import numpy   as np

# ========================================================= #
# ===  impactX tracking file                            === #
# ========================================================= #
def main_impactx():

    x_, y_, t_ = 0, 1, 2
    mm, mrad   = 1.0e-3, 1.0e-3
    amu        = 931.494              # [MeV]
    
    sim        = impactx.ImpactX()

    # ------------------------------------------------- #
    # --- [1]  preparation                          --- #
    # ------------------------------------------------- #
    sim.particle_shape                    = 2
    sim.space_charge                      = False
    sim.slice_step_diagnostics            = True
    sim.particle_lost_diagnostics_backend = ".h5"

    Ek0 = 0.5
    Em0 = amu

    # ------------------------------------------------- #
    # --- [2] grid & reference particle             --- #
    # ------------------------------------------------- #
    sim.init_grids()
    ref = sim.particle_container().ref_particle()
    ref.set_charge_qe     ( 1.0 )
    ref.set_mass_MeV      ( Em0 )
    ref.set_kin_energy_MeV( Ek0 )
    
    # ------------------------------------------------- #
    # --- [3] distribution                          --- #
    # ------------------------------------------------- #
    e995_e1RMS   = 1.0 / 2.807
    eps_norm     = 1.0 * mm * mrad * e995_e1RMS         # [m rad]  :: normalized epsilon
    alpha_xyt    = np.array( [ 0.0, 0.0, 0.0 ] )         #     Twiss Parameter :: Alpha
    beta_xyt     = np.array( [ 1.0, 1.0, 1.0 ] )         # [m] Twiss Parameter :: Beta
    gamma_xyt    = ( 1.0 + alpha_xyt**2 ) / ( beta_xyt ) #     Twiss Parameter :: Gamma
    
    gamma_enter  = ( 1.0 + Ek0/Em0 )                     # Einstein's Gamma
    beta_enter   = ( 1.0 - gamma_enter**(-2) )
    eps_enter    = eps_norm / ( beta_enter * gamma_enter )
    eps_xyt      = np.array( [ eps_enter, eps_enter, eps_enter ] )  # [m rad]
    lambda_q     = np.sqrt( eps_xyt / gamma_xyt )
    lambda_p     = np.sqrt( eps_xyt /  beta_xyt )
    mu_qp        = alpha_xyt / ( beta_xyt * gamma_xyt )
    
    distri       = impactx.distribution.Waterbag(
        lambdaX  = lambda_q[x_],
        lambdaY  = lambda_q[y_],
        lambdaT  = lambda_q[t_],
        lambdaPx = lambda_p[x_],
        lambdaPy = lambda_p[y_],
        lambdaPt = lambda_p[t_],
        muxpx    = mu_qp[x_], 
        muypy    = mu_qp[y_], 
        mutpt    = mu_qp[t_], 
    )
    sim.add_particles( 1e-12, distri, 1000 )
    F_escale     = 1.0 / Em0
    
    # ------------------------------------------------- #
    # --- [4] lattice definition                    --- #
    # ------------------------------------------------- #
    ns       = 30
    Ra       = 1.0e6
    bpm      = impactx.elements.BeamMonitor( "bpm", backend="h5")
    dr1      = impactx.elements.ExactDrift( name="dr1", ds=1.0, aperture_x=Ra, aperture_y=Ra, nslice=ns )
    rf1      = impactx.elements.RFCavity  ( name="rf1", ds=1.0, escale=0.1*F_escale, freq=0.0e6, \
                                            phase=0.0, cos_coefficients=[2.0], sin_coefficients=[0.0], \
                                            aperture_x=Ra, aperture_y=Ra, nslice=ns )
    dr2      = impactx.elements.ExactDrift( name="dr2", ds=1.0, aperture_x=Ra, aperture_y=Ra, nslice=ns )
    beamline = [ bpm, dr1, bpm, rf1, bpm, dr2, bpm ]
    
    # ------------------------------------------------- #
    # --- [5] tracking                              --- #
    # ------------------------------------------------- #
    sim.lattice.extend( beamline )
    sim.track_particles()
        
    # ------------------------------------------------- #
    # --- [6] end                                   --- #
    # ------------------------------------------------- #
    sim.finalize()


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    main_impactx()
