import os, sys, json5
import impactx
import numpy as np
import pandas as pd
import amrex.space3d as amr


# ========================================================= #
# ===  set__manualReferenceParticle.py                  === #
# ========================================================= #

def set__manualReferenceParticle( particle_container=None,  \ # particle_container of impactx
                                  ref_xyt=[0.,0.,0.], ref_pxyt=[0.,0.,0.], \
                                  n_part=2, \                 # #.of particles : min. => 2
                                 ):
    x_, y_, t_ = 0, 1, 2
    
    # ------------------------------------------------- #
    # --- [1] set particle distribution             --- #
    # ------------------------------------------------- #
    dx_podv  = amr.PODVector_real_std()
    dy_podv  = amr.PODVector_real_std()
    dt_podv  = amr.PODVector_real_std()
    dpx_podv = amr.PODVector_real_std()
    dpy_podv = amr.PODVector_real_std()
    dpt_podv = amr.PODVector_real_std()
    w_podv   = amr.PODVector_real_std()
    
    for ik in range( n_part ):
        dx_podv.push_back ( ref_xyt[x_]  )
        dy_podv.push_back ( ref_xyt[y_]  )
        dt_podv.push_back ( ref_xyt[t_]  )
        dpx_podv.push_back( ref_pxyt[x_] )
        dpy_podv.push_back( ref_pxyt[y_] )
        dpt_podv.push_back( ref_pxyt[t_] )
        w_podv.push_back  (   1.0        )

    
    qm_eev =  -1.0 / 0.510998950 / 1e6
    particle_container.add_n_particles( dx_podv , dy_podv , dt_podv ,
                                        dpx_podv, dpy_podv, dpt_podv,
                                        qm_eev  , w=w_podv )
    return( particle_container )


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    
    x_, y_, t_ = 0, 1, 2
    mm, mrad   = 1.0e-3, 1.0e-3
    amu        = 931.494          # [MeV]
    full2rms   = 1.0 / 8.0        # full -> rms emittance ( 6D wb-> 1/8 )

    linear     = False
    
    # ------------------------------------------------- #
    # --- [1]  initialization                       --- #
    # ------------------------------------------------- #
    sim = impactx.ImpactX()
    
    sim.particle_shape                    = 2
    sim.slice_step_diagnostics            = True
    sim.particle_lost_diagnostics_backend = ".h5"
    sim.space_charge                      = False

    sim.init_grids()
    
    # ------------------------------------------------- #
    # --- [2] reference particle                    --- #
    # ------------------------------------------------- #
    Ek0       = 40.0             # MeV
    Em0       = 2.014 * amu      # MeV

    gamma_rel = ( 1.0 + Ek0/Em0 )
    beta_rel  = np.sqrt( 1.0 - gamma_rel**(-2.0) )
    p0c       = beta_rel * gamma_rel * Em0  # [MeV]
    Brho      = p0c / 0.299792458           # [T·m]
    print(f"[ref]  p0c={p0c:.3f} MeV/c,  Brho={Brho:.3f} T·m")
    
    ref = sim.particle_container().ref_particle()
    ref.set_charge_qe     ( +1.0 )
    ref.set_mass_MeV      ( Em0 )
    ref.set_kin_energy_MeV( Ek0 )
    ref.z = 0.0

    # ------------------------------------------------- #
    # --- [3] function call                         --- #
    # ------------------------------------------------- #
    pc = sim.particle_container()
    pc = set__manualReferenceParticle( particle_container=pc )
    
    # ------------------------------------------------- #
    # --- [4] lattice definition                    --- #
    # ------------------------------------------------- #
    Lq  = 0.2
    Ld  = 1.0
    G   = + 0.0
    k1  = G / Brho
    
    bpm      = impactx.elements.BeamMonitor( "bpm", backend="h5" )
    if ( linear ):
        qm1      = impactx.elements.Quad ( ds=Lq, k= k1 )
        qm2      = impactx.elements.Quad ( ds=Lq, k=-k1 )
        dr1      = impactx.elements.Drift( ds=Ld )
    else:
        qm1      = impactx.elements.ExactQuad ( ds=Lq, k= k1, unit=0 )
        qm2      = impactx.elements.ExactQuad ( ds=Lq, k=-k1, unit=0 )
        qm1_dr   = impactx.elements.ExactDrift( ds=Lq )
        qm2_dr   = impactx.elements.ExactDrift( ds=Lq )
        dr1      = impactx.elements.ExactDrift( ds=Ld )

    beamline = [ bpm, dr1 ] + [ qm1   , bpm, dr1, bpm, qm2   , bpm, dr1, bpm ]*10 + [ bpm ]
    # beamline = [ bpm, dr1 ] + [ qm1_dr, bpm, dr1, bpm, qm2_dr, bpm, dr1, bpm ]*10 + [ bpm ]

    
    # ------------------------------------------------- #
    # --- [5] tracking                              --- #
    # ------------------------------------------------- #
    sim.lattice.extend( beamline )
    sim.track_particles()
        
    # ------------------------------------------------- #
    # --- [6] end                                   --- #
    # ------------------------------------------------- #
    sim.finalize()

