import os, sys, json5
import impactx
import numpy as np
import pandas as pd
import amrex.space3d as amr


# ========================================================= #
# ===  set__manualReferenceParticle.py                  === #
# ========================================================= #

def set__manualReferenceParticle( particle_container=None,  # particle_container of impactx
                                  ref_xyt=[0.,0.,0.], ref_pxyt=[0.,0.,0.], 
                                  n_part=2,                 # #.of particles : min. => 2
                                 ):
    x_, y_, t_ = 0, 1, 2
    MeV        = 1.e6
    
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

    refp   = pc.ref_particle()
    qm_eeV = refp.charge_qe / ( refp.mass_MeV * MeV )
    particle_container.add_n_particles( dx_podv , dy_podv , dt_podv ,
                                        dpx_podv, dpy_podv, dpt_podv,
                                        qm_eeV  , w=w_podv )
    return( particle_container )


# ========================================================= #
# ===  translate__ExactQuad_to_ExactDrift               === #
# ========================================================= #

def translate__ExactQuad_to_ExactDrift( inpFile="dat/beamline_impactx.json",
                                        outFile="dat/beamline_noExactQuad.json" ):

    # ------------------------------------------------- #
    # --- [1] import beamline file                  --- #
    # ------------------------------------------------- #
    with open( inpFile, "r" ) as f:
        beamline = json5.load( f )
    sequence = beamline["sequence"]
    elements = beamline["elements"]

    # ------------------------------------------------- #
    # --- [2] translate ( ExactQuad -> ExactDrift ) --- #
    # ------------------------------------------------- #
    elements_ = {}
    for key,elem in elements.items():
        if ( elem["type"].lower() == "quadrupole" ):
            elem = { "type":"drift", "name":elem["name"], "ds":elem["ds"] }
        elements_[key] = elem
            
    # ------------------------------------------------- #
    # --- [3] export virtual beamline               --- #
    # ------------------------------------------------- #
    beamline_ = { "elements":elements_, "sequence":sequence }
    with open( outFile, "w" ) as f:
        json5.dump( beamline_, f, indent=4 )
    print( "[translate__ExactQuad_to_ExactDrift] output :: {} ".format( outFile ) )
    return( beamline_ )


# ========================================================= #
# ===  aquire__tNL_and_RFphase                          === #
# ========================================================= #

def aquire__tNL_and_RFphase():

    # ------------------------------------------------- #
    # --- [1]                         --- #
    # ------------------------------------------------- #


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    
    # x_, y_, t_ = 0, 1, 2
    # mm, mrad   = 1.0e-3, 1.0e-3
    # amu        = 931.494          # [MeV]
    # full2rms   = 1.0 / 8.0        # full -> rms emittance ( 6D wb-> 1/8 )

    # linear     = False
    
    # # ------------------------------------------------- #
    # # --- [1]  initialization                       --- #
    # # ------------------------------------------------- #
    # sim = impactx.ImpactX()
    
    # sim.particle_shape                    = 2
    # sim.slice_step_diagnostics            = True
    # sim.particle_lost_diagnostics_backend = ".h5"
    # sim.space_charge                      = False

    # sim.init_grids()
    
    # # ------------------------------------------------- #
    # # --- [2] reference particle                    --- #
    # # ------------------------------------------------- #
    # Ek0       = 40.0             # MeV
    # Em0       = 2.014 * amu      # MeV

    # gamma_rel = ( 1.0 + Ek0/Em0 )
    # beta_rel  = np.sqrt( 1.0 - gamma_rel**(-2.0) )
    # p0c       = beta_rel * gamma_rel * Em0  # [MeV]
    # Brho      = p0c / 0.299792458           # [T·m]
    # print(f"[ref]  p0c={p0c:.3f} MeV/c,  Brho={Brho:.3f} T·m")
    
    # ref = sim.particle_container().ref_particle()
    # ref.set_charge_qe     ( +1.0 )
    # ref.set_mass_MeV      ( Em0 )
    # ref.set_kin_energy_MeV( Ek0 )
    # ref.z = 0.0

    # # ------------------------------------------------- #
    # # --- [3] function call                         --- #
    # # ------------------------------------------------- #
    # pc = sim.particle_container()
    # pc = set__manualReferenceParticle( particle_container=pc )
    
    # # ------------------------------------------------- #
    # # --- [4] lattice definition                    --- #
    # # ------------------------------------------------- #
    # Lq  = 0.2
    # Ld  = 1.0
    # G   = + 0.0
    # k1  = G / Brho
    
    # bpm      = impactx.elements.BeamMonitor( "bpm", backend="h5" )
    # if ( linear ):
    #     qm1      = impactx.elements.Quad ( ds=Lq, k= k1 )
    #     qm2      = impactx.elements.Quad ( ds=Lq, k=-k1 )
    #     dr1      = impactx.elements.Drift( ds=Ld )
    # else:
    #     qm1      = impactx.elements.ExactQuad ( ds=Lq, k= k1, unit=0 )
    #     qm2      = impactx.elements.ExactQuad ( ds=Lq, k=-k1, unit=0 )
    #     qm1_dr   = impactx.elements.ExactDrift( ds=Lq )
    #     qm2_dr   = impactx.elements.ExactDrift( ds=Lq )
    #     dr1      = impactx.elements.ExactDrift( ds=Ld )

    # beamline = [ bpm, dr1 ] + [ qm1   , bpm, dr1, bpm, qm2   , bpm, dr1, bpm ]*10 + [ bpm ]
    # # beamline = [ bpm, dr1 ] + [ qm1_dr, bpm, dr1, bpm, qm2_dr, bpm, dr1, bpm ]*10 + [ bpm ]

    
    # # ------------------------------------------------- #
    # # --- [5] tracking                              --- #
    # # ------------------------------------------------- #
    # sim.lattice.extend( beamline )
    # sim.track_particles()
        
    # # ------------------------------------------------- #
    # # --- [6] end                                   --- #
    # # ------------------------------------------------- #
    # sim.finalize()


    translate__ExactQuad_to_ExactDrift()
