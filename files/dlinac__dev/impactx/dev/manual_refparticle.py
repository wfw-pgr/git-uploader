import os, sys, json5, shutil
import impactx
import numpy as np
import pandas as pd
import nk_toolkit.impactx.impactx_toolkit as itk


# ========================================================= #
# ===  manual__refparticle.py                           === #
# ========================================================= #

def main_impactx():
    
    x_, y_, t_ = 0, 1, 2
    mm, mrad   = 1.0e-3, 1.0e-3
    amu        = 931.494          # [MeV]
    full2rms   = 1.0 / 8.0        # full -> rms emittance ( 6D wb-> 1/8 )
    
    # ------------------------------------------------- #
    # --- [1]  load parameters                      --- #
    # ------------------------------------------------- #
    paramsFile = "../dat/parameters.json"
    with open( paramsFile, "r" ) as f:
        params = json5.load( f )
    
    # ------------------------------------------------- #
    # --- [2]  initialization                       --- #
    # ------------------------------------------------- #
    sim = impactx.ImpactX()
    
    sim.particle_shape                    = 2
    sim.slice_step_diagnostics            = True
    sim.particle_lost_diagnostics_backend = ".h5"
    sim.space_charge                      = params["mode.space_charge"]

    sim.init_grids()
    
    # ------------------------------------------------- #
    # --- [2] reference particle                    --- #
    # ------------------------------------------------- #
    Ek0 = params["beam.Ek.MeV/u"] * params["beam.u"]
    Em0 = params["beam.mass.amu"] * amu
    pc  = sim.particle_container()
    ref = pc.ref_particle()
    ref.set_charge_qe     ( params["beam.charge.qe"] )
    ref.set_mass_MeV      ( Em0 )
    ref.set_kin_energy_MeV( Ek0 )
    
    # ------------------------------------------------- #
    # --- [3] distribution                          --- #
    # ------------------------------------------------- #
    pc  = itk.set__manualReferenceParticle( particle_container=pc )
    
    # ------------------------------------------------- #
    # --- [4] lattice definition                    --- #
    # ------------------------------------------------- #
    beamlineFile = "../dat/beamline_noExactQuad.json"
    beamline     = itk.set__latticeComponents( beamlineFile=beamlineFile )
    
    # ------------------------------------------------- #
    # --- [5] save beamline                         --- #
    # ------------------------------------------------- #
    stack = { str(ik):element.to_dict() for ik,element in enumerate(beamline) }
    with open( params["file.beamline"], "w" ) as f:
        json5.dump( stack, f, indent=2 )
    
    # ------------------------------------------------- #
    # --- [6] tracking                              --- #
    # ------------------------------------------------- #
    sim.lattice.extend( beamline )
    sim.track_particles()
        
    # ------------------------------------------------- #
    # --- [7] end                                   --- #
    # ------------------------------------------------- #
    sim.finalize()


# ========================================================= #
# ===  determine__rfphase                               === #
# ========================================================= #

def determine__rfphase():

    x_, y_, t_ = 0, 1, 2
    mm, mrad   = 1.0e-3, 1.0e-3
    amu        = 931.494          # [MeV]
    full2rms   = 1.0 / 8.0        # full -> rms emittance ( 6D wb-> 1/8 )


    # ------------------------------------------------- #
    # --- [1] function to run onepath simulation    --- #
    # ------------------------------------------------- #
    def run__onepath( mode=None, Ek0=None, Em0=None, charge_qe=None, charge_bunch=None, \
                      distri=None, nparticles=None, beamlineFile="../dat/beamline_impactx.json",\
                      noExactQuadFile="../dat/beamline_noExactQuad.json" ):
        
        # ------------------------------------------------- #
        # --- [1]  initialization                       --- #
        # ------------------------------------------------- #
        sim = impactx.ImpactX()
        sim.particle_shape         = 2
        sim.slice_step_diagnostics = True
        sim.space_charge           = False
        sim.init_grids()
    
        # ------------------------------------------------- #
        # --- [2] reference particle                    --- #
        # ------------------------------------------------- #
        pc  = sim.particle_container()
        ref = pc.ref_particle()
        ref.set_charge_qe     ( charge_qe )
        ref.set_mass_MeV      ( Em0       )
        ref.set_kin_energy_MeV( Ek0       )
    
        # ------------------------------------------------- #
        # --- [3] distribution & lattice settings       --- #
        # ------------------------------------------------- #
        if   ( mode == "refpart-quad"  ):
            pc       = itk.set__manualReferenceParticle( particle_container=pc )
            beamline = itk.set__latticeComponents( beamlineFile=beamlineFile )
            sim.lattice.extend( beamline )
        elif ( mode == "refpart-drift" ):
            pc       = itk.set__manualReferenceParticle( particle_container=pc )
            beamline = itk.translate__ExactQuad_to_ExactDrift( inpFile=beamlineFile, \
                                                               outFile=noExactQuadFile )
            beamline = itk.set__latticeComponents( elements=beamline["elements"] )
            sim.lattice.extend( beamline )
        elif ( mode == "refpart-bunch" ):
            sim.add_particles( charge_bunch, distri, nparticles )
            beamline = itk.set__latticeComponents( beamlineFile=beamlineFile )
            sim.lattice.extend( beamline )
        else:
            print( "unknown mode :: {}".format( mode ) )
            sys.exit()
            
        # ------------------------------------------------- #
        # --- [4] tracking                              --- #
        # ------------------------------------------------- #
        sim.track_particles()
        sim.finalize()
        return()

    # ------------------------------------------------- #
    # --- [2] extract needed information            --- #
    # ------------------------------------------------- #
    def extract__info():
        info = None
        return( info )
    
    
    # ------------------------------------------------- #
    # --- [3] actual run onepath                    --- #
    # ------------------------------------------------- #
    Ek0       = 40.0
    Em0       = 931.494 * 2.0
    charge_qe = +1.0
    modes = [ "refpart-quad", "refpart-drift", "refpart-bunch" ]
    for mode in modes:
        if ( mode == "refpart-bunch" ):
            # ------------------------------------------------- #
            # --- [1]  load parameters                      --- #
            # ------------------------------------------------- #
            paramsFile = "../dat/parameters.json"
            with open( paramsFile, "r" ) as f:
                params = json5.load( f )

            # ------------------------------------------------- #
            # --- [3] distribution                          --- #
            # ------------------------------------------------- #
            alpha_xyt     = np.array( params["beam.twiss.alpha"] )
            beta_xyt      = np.array( params["beam.twiss.beta" ] )
            epsnxy        = np.array( params["beam.emittance.xy.norm"] )
            epsnz         = params["beam.emittance.z.geom"]
            
            gamma_rel    = ( 1.0 + Ek0/Em0 )
            beta_rel     = np.sqrt( 1.0 - gamma_rel**(-2.0) )
            epsnxy       = epsnxy / ( beta_rel * gamma_rel )
            eps_geom     = np.array( [ epsnxy[x_], epsnxy[y_], epsnz ] )
            eps_geom     = eps_geom * mm * mrad * full2rms
            
            gamma_xyt    = (1.0 + alpha_xyt**2) / ( beta_xyt )
            lambda_q     = np.sqrt( eps_geom / gamma_xyt )
            lambda_p     = np.sqrt( eps_geom /  beta_xyt )
            mu_qp        = alpha_xyt / np.sqrt( beta_xyt * gamma_xyt )
            
            distri       = impactx.distribution.Waterbag(
                lambdaX  = lambda_q[x_], lambdaY  = lambda_q[y_], lambdaT  = lambda_q[t_],
                lambdaPx = lambda_p[x_], lambdaPy = lambda_p[y_], lambdaPt = lambda_p[t_],
                muxpx    = mu_qp[x_]   , muypy    = mu_qp[y_],    mutpt    = mu_qp[t_], 
            )
            charge_bunch = params["beam.charge.C"]
            nparticles   = int( params["beam.nparticles"] )
        else:
            distri       = None
            nparticles   = None
            charge_bunch = None
        run__onepath( mode=mode, \
                      charge_bunch=charge_bunch, \
                      nparticles=nparticles, distri=distri, \
                      Em0=Em0, Ek0=Ek0, charge_qe=charge_qe )
        shutil.copytree( "../impactx/diags/", "../impactx/diags__{}".format( mode ), \
                         dirs_exist_ok=True )
        

    # ------------------------------------------------- #
    # --- [4] acquire positions                     --- #
    # ------------------------------------------------- #

def post():
    
    paramsFile     = "../dat/parameters.json"
    refpart_drift  = itk.get__particles( paramsFile=paramsFile, pids=[0], \
                                         bpmFile="../impactx/diags__refpart-drift/openPMD/bpm.h5",\
                                         refFile="../impactx/diags__refpart-drift/ref_particle.0" )
    refpart_quad   = itk.get__particles( paramsFile=paramsFile, pids=[0], \
                                         bpmFile="../impactx/diags__refpart-quad/openPMD/bpm.h5",\
                                         refFile="../impactx/diags__refpart-quad/ref_particle.0" )
    refpart_bunch  = itk.get__particles( paramsFile=paramsFile, pids=None, \
                                         bpmFile="../impactx/diags__refpart-bunch/openPMD/bpm.h5",\
                                         refFile="../impactx/diags__refpart-bunch/ref_particle.0" )
    refpart_bunch  = refpart_bunch.groupby("step").mean( numeric_only=True )
    print( refpart_drift )
    print( refpart_quad  )
    print( refpart_bunch )
    print( refpart_bunch.keys() )

    import nk_toolkit.plot.load__config   as lcf
    import nk_toolkit.plot.gplot1D        as gp1
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [4.5,4.5],
        "figure.pngFile"     : "tdiff.png", 
        "figure.position"    : [ 0.16, 0.16, 0.94, 0.94 ],
        "ax1.y.normalize"    : 1.0e0, 
        "ax1.x.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.y.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.x.label"        : "s [m]",
        "ax1.y.label"        : "t [m]",
        "ax1.x.minor.nticks" :   1, 
        "plot.marker"        : "o",
        "plot.markersize"    : 3.0,
        "legend.fontsize"    : 9.0, 
    }
    config = { **config, **config_ }
        
    fig    = gp1.gplot1D( config=config )
    fig.add__plot( xAxis=refpart_drift["ref_s"], yAxis=refpart_drift["tp"], label="refpart-drift" )
    fig.add__plot( xAxis=refpart_quad ["ref_s"], yAxis=refpart_quad ["tp"], label="refpart-quad " )
    fig.add__plot( xAxis=refpart_bunch["ref_s"], yAxis=refpart_bunch["tp"], label="refpart-bunch" )
    fig.set__axis()
    fig.set__legend()
    fig.save__figure()

    

        
# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    # determine__rfphase()
    post()
