import os, sys, json5, shutil
import impactx
import numpy as np
import pandas as pd
import nk_toolkit.impactx.impactx_toolkit as itk


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
    def run__onepath( Ek0=None, Em0=None, charge_qe=None, \
                      beamlineFile="../dat/beamline_impactx.json",\
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
        pc        = itk.set__manualReferenceParticle( particle_container=pc )
        beamline  = itk.translate__ExactQuad_to_ExactDrift( inpFile=beamlineFile, \
                                                           outFile=noExactQuadFile )
        elements  = beamline["elements"]
        # beamline  = adjust__rfphase( elements=elements, phaseFile="adjust_phase.csv" )
        beamline  = itk.set__latticeComponents( elements=elements )
        sim.lattice.extend( beamline )
            
        # ------------------------------------------------- #
        # --- [4] tracking                              --- #
        # ------------------------------------------------- #
        sim.track_particles()
        sim.finalize()
        return()

    
    # ------------------------------------------------- #
    # --- [3] actual run onepath                    --- #
    # ------------------------------------------------- #
    Ek0       = 40.0
    Em0       = 931.494 * 2.0
    charge_qe = +1.0
    run__onepath( Em0=Em0, Ek0=Ek0, charge_qe=charge_qe )


    
# ========================================================= #
# ===  plot phase                                       === #
# ========================================================= #

def plot__phase():

    paramsFile     = "../dat/parameters.json"
    particles      = itk.get__particles( paramsFile=paramsFile, pids=[0], \
                                         bpmFile="diags/openPMD/bpm.h5", \
                                         refFile="diags/ref_particle.0" )

    def normalize__degree( degree ):
        return( ( degree + 180.0 )%(360.0) - 180.0 )

    
    import nk_toolkit.plot.load__config   as lcf
    import nk_toolkit.plot.gplot1D        as gp1
    config   = lcf.load__config()
    config_  = {
        "figure.size"        : [4.5,4.5],
        "figure.pngFile"     : "png/tp.png", 
        "figure.position"    : [ 0.16, 0.16, 0.94, 0.94 ],
        "ax1.y.normalize"    : 1.0e0, 
        "ax1.x.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.y.range"        : { "auto":True, "min": 0.0, "max":1.0, "num":11 },
        "ax1.x.label"        : "x",
        "ax1.y.label"        : "y",
        "ax1.x.minor.nticks" : 1, 
        "plot.marker"        : "o",
        "plot.markersize"    : 3.0,
        "legend.fontsize"    : 9.0, 
    }
    config = { **config, **config_ }
    with open( "../dat/beamline_impactx.json", "r" ) as f:
        beamline = json5.load( f )
        sequence = beamline["sequence"]

    cv     = 3.0e8
    ns     = 1.0e-9
    freq   = 4.0 * 36.5e6
    particles["ns"]    = ( particles["ref_z"] + particles["tp"] ) / ns
    particles["phase"] = normalize__degree( particles["ns"] * ns * freq * 360.0 )
    particles["tag"]   = pd.Series( sequence )
    particles.to_csv( "adjust_phase.csv" )
    print( particles["tp"] )
    print( particles["ns"] )
    print( particles["phase"] )
        
    # fig    = gp1.gplot1D( config=config )
    # fig.add__plot( xAxis=particles["ref_s"], yAxis=particles["phase"] )
    # fig.set__axis()
    # fig.set__legend()
    # fig.save__figure()

    

# ========================================================= #
# ===  adjust__rfphase                                  === #
# ========================================================= #

def adjust__rfphase( elements=None, phase=None, phaseFile=None ):

    if ( phase is None ):
        if ( phaseFile is None ):
            sys.exit( "no phase" )
        else:
            phase = pd.read_csv( phaseFile, index_col="tag" )
    
    for ik,key in enumerate(elements.keys()):
        if ( elements[key]["type"] in ["rfcavity"] ):
            print( key )
            print( elements[key]["phase"] )
            elements[key]["phase"] = phase.loc[ key, "phase" ]
            print( elements[key]["phase"] )
            print()
    # sys.exit()
        
    return( elements )
        


# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    # determine__rfphase()
    plot__phase()
