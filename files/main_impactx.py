import os, sys, json5
import impactx
import numpy   as np
import pandas  as pd

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
    
    Ek0        = 40.0                                  # [MeV]
    Em0        = 2.014 * amu                           # [MeV]
    e995_pi_mm = 20.0                                  # [pi mm mrad]
    alpha_xyt  = np.array( [ 0.0, 0.0, 0.0 ] ) 
    beta_xyt   = np.array( [ 8.0, 4.0, 9.3 ] )         # [m]
    charge     = 1.0e-12                               # [C]
    npt        = 1000                                  # #.of particles
    eps_norm   = np.array( [ 150.0, 150.0, 426.0 ] )   # [ pi mm mrad ]

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
    e995_e1RMS   = 1.0 / 2.807                                 # 99.5% emittance -> 1-RMS emittance
    eps_norm     = eps_norm * mm * mrad * e995_e1RMS * np.pi
    # eps_norm     = e995_pi_mm * mm * mrad * e995_e1RMS # [ m rad ]
    
    gamma_xyt    = (1.0 + alpha_xyt**2) / ( beta_xyt )
    gamma_rel    = ( 1.0 + Ek0/Em0 )
    beta_rel     = np.sqrt( 1.0 - gamma_rel**(-2.0) )
    eps_geom     = eps_norm / ( beta_rel * gamma_rel )
    lambda_q     = np.sqrt( eps_geom / gamma_xyt )
    lambda_p     = np.sqrt( eps_geom /  beta_xyt )
    mu_qp        = alpha_xyt / np.sqrt( beta_xyt * gamma_xyt )
    
    distri       = impactx.distribution.Waterbag(
        lambdaX  = lambda_q[x_], lambdaY  = lambda_q[y_], lambdaT  = lambda_q[t_],
        lambdaPx = lambda_p[x_], lambdaPy = lambda_p[y_], lambdaPt = lambda_p[t_],
        muxpx    = mu_qp[x_]   , muypy    = mu_qp[y_],    mutpt    = mu_qp[t_], 
    )
    sim.add_particles( charge, distri, npt )
    
    # ------------------------------------------------- #
    # --- [4] lattice definition                    --- #
    # ------------------------------------------------- #
    beamlineFile = "../dat/beamline_impactx.json"
    with open( beamlineFile, "r" ) as f:
        beamline = json5.load( f )
    elements = beamline["elements"]

    stack    = []
    bpm      = impactx.elements.BeamMonitor( "bpm", backend="h5" )
    for key,elem in elements.items():
        elem_ = { hkey:val for hkey,val in elem.items() if hkey != "type" }
        if   ( elem["type"] in [ "rfcavity" ]   ):
            bcomp = impactx.elements.RFCavity  ( **elem_ )
        elif ( elem["type"] in [ "quadrupole" ] ):
            bcomp = impactx.elements.ExactQuad ( **elem_ )
        elif ( elem["type"] in [ "drift" ]      ):
            bcomp = impactx.elements.ExactDrift( **elem_ )
        else:
            sys.exit( "[main_impactx.py] unknown element type :: {} ".format( elem["type"] ) )
        stack += [ bcomp ]
    beamline = [ bpm ] + stack + [ bpm ]
        
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
    4
