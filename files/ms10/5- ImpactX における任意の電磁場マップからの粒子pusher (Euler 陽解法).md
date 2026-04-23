
# 目的

- ImpactX の `Programmable` 要素を用いて、任意の電磁場マップを読込み、粒子をpushするルーチンを構築する。


# 実装
## 電磁場マップの想定

- 磁場：3 次元直交座標マップ  $(B_x, B_y, B_z)$
- 電場：RZ２次元の軸対称マップ  $(E_r,E_z)$

## 取組概要

### pusherクラスの概要

- `impactx.elements.Programmable` を継承したクラス `EBmapElement__ExplicitEuler` を作成

	- 以下がメンバ関数
		- `_load__ebfieldfile`：電磁場マップファイルの読み込み 
		- `_construct__interpolator` ：補間関数 (interpolator)の生成
		- `_evaluate_fields`：粒子位置での場の評価 
		- `_push__fromfield`：その場を用いた粒子 push

### pusherクラスの入力

- `ds`：要素長さ [m]
- `name`：名前
- `nslice`：分割数
- `bfieldfile`：(str) 磁場ファイル名
- `efieldfile`：(str) 電場ファイル名
- `bfactor`：(float) 磁場強度
- `efactor` ：(float) 電場強度
- `phase`：位相 [deg.]
- `freq` ：周波数：[Hz]
    

### 実装と検証

#### 実装
1. `Programmable` 継承クラスを作成。
2.  main_impactx.py のメインルーチンを作成。
3. サンプル電磁場作成ルーチン：generate__sampleField.py 

#### 検証
1.  粒子数数個で実行
2.  多粒子で、E=0, B=0でdrift と比較
3.  多粒子で、E=1 MV/m, B=1 T を作成、ChrAccと比較


# コード

## EBmapElement__ExplicitEuler.py

```python
import os, sys, impactx
import numpy  as np
import pandas as pd
import scipy.interpolate as itp

# ========================================================= #
# ===  EBmapElement__ExplicitEuler                      === #
# ========================================================= #
#
#  EB-map Format :
#
#    - B-field 3D Cartesian (xyz)   Coordinate
#      -- ( x, y, z, Bx, By, Bz ) ( .dat or .csv )   unit: [m] and [T]
#
#    - E-field 2D axisymmetric (rz) Coordinate
#      -- ( r, z,    Er, Ez     ) ( .dat or .csv )   unit: [m] and [MV/m]
#
#    - In ImpactX, t-coordinate (tp) denotes the length :: cv *( t-t_ref )
#      -- spped of light cv [times] difference of arrival time ( against reference particle )
#      -- tp > 0 => delayed  arrival to ref.
#      -- tp < 0 => advanced arrival to ref.
#
# --------------------------------------------------------- #

class EBmapElement__ExplicitEuler( impactx.elements.Programmable ):

    # ===================================================== #
    # ===  __init__                                     === #
    # ===================================================== #
    def __init__( self,
                  ds         =0.0     , # element length [m]
                  name       ="EBmap" ,
                  nslice     =1       ,
                  bfieldfile =None    , # (str)
                  efieldfile =None    , # (str)
                  bfactor    =1.0     , # (float)
                  efactor    =1.0     , # (float)
                  freq       =0.0     , # (float) [Hz]
                  phase      =0.0     , # (float) [deg.]
                 ):
        super().__init__( ds=ds, name=name, nslice=nslice )

        self.ds              = ds
        self.name            = name
        self.nslice          = nslice

        self.bfieldfile      = bfieldfile
        self.efieldfile      = efieldfile

        self.bfactor         = float( bfactor )
        self.efactor         = float( efactor )
        self.freq            = float( freq  )
        self.phase           = float( phase )

        # containers for field maps / interpolators
        self.bmap            = None
        self.emap            = None

        self.Bx_interpolator = None
        self.By_interpolator = None
        self.Bz_interpolator = None
        self.Er_interpolator = None
        self.Ez_interpolator = None

        # load field data and prepare interpolators
        self._load__ebfieldfile()
        self._construct__interpolator()

        # assign programmable push
        self.push = self._push__fromfield


    # ===================================================== #
    # === _load__ebfieldfile                            === #
    # ===================================================== #
    def _load__ebfieldfile(self):
        """ Load magnetic/electric field maps from files.

        Formats:
            bfieldfile: ( x, y, z, Bx, By, Bz )
            efieldfile: ( r, z, Er, Ez )
        """

        # ------------------------------------------------- #
        # --- [1] load B-Field                          --- #
        # ------------------------------------------------- #
        if ( self.bfieldfile is not None ):
            if ( os.path.splitext( self.bfieldfile )[1].lower() == ".csv" ):
                bdat = pd.read_csv( self.bfieldfile ).to_numpy()
            else:
                bdat = np.loadtxt( self.bfieldfile )
            if ( bdat.shape[1] < 6 ):
                raise ValueError( "[ERROR] bfieldfile must have 6 columns: x,y,z,Bx,By,Bz" )
            
            xAxis      = np.unique( bdat[:,0] )
            yAxis      = np.unique( bdat[:,1] )
            zAxis      = np.unique( bdat[:,2] )
            nx, ny, nz = len(xAxis), len(yAxis), len(zAxis)
            
            if ( nx*ny*nz != len(bdat) ):
                raise ValueError( "[ERROR] B-field map size is inconsistent with structured grid." )

            Bx = self.bfactor * ( bdat[:,3] ).reshape( (nx,ny,nz), order="C" )
            By = self.bfactor * ( bdat[:,4] ).reshape( (nx,ny,nz), order="C" ) 
            Bz = self.bfactor * ( bdat[:,5] ).reshape( (nx,ny,nz), order="C" )

            self.bmap = { "xAxis": xAxis, "yAxis": yAxis, "zAxis": zAxis,
                          "Bx"   : Bx   , "By"   : By   ,"Bz"    : Bz, }

        # ------------------------------------------------- #
        # --- [2] load E-Field                          --- #
        # ------------------------------------------------- #
        if ( self.efieldfile is not None ):
            if ( os.path.splitext( self.efieldfile )[1].lower() == ".csv" ):
                edat = pd.read_csv( self.efieldfile ).to_numpy()
            else:
                edat = np.loadtxt( self.efieldfile )
            if ( edat.shape[1] < 4 ):
                raise ValueError( "[ERROR] efieldfile must have 4 columns: r,z,Er,Ez" )

            rAxis      = np.unique( edat[:,0] )
            zAxis      = np.unique( edat[:,1] )
            nr, nz     = len(rAxis), len(zAxis)
            if ( nr*nz != len(edat) ):
                raise ValueError( "[ERROR] E-field map size is inconsistent with structured grid." )

            Er = self.efactor * ( edat[:,2] ).reshape( (nr,nz), order="C" )
            Ez = self.efactor * ( edat[:,3] ).reshape( (nr,nz), order="C" )

            self.emap = { "rAxis":rAxis, "zAxis":zAxis, "Er":Er, "Ez":Ez, }


    # ===================================================== #
    # === _construct__interpolator                      === #
    # ===================================================== #
    def _construct__interpolator(self):
        """ construct interpolators for B(x,y,z) and E(r,z).
        """
        # ------------------------------------------------- #
        # --- [1] B-Field interpolator                  --- #
        # ------------------------------------------------- #
        if ( self.bmap is not None ):
            xyzcoord = ( self.bmap["xAxis"], self.bmap["yAxis"], self.bmap["zAxis"] )
            self.Bx_interpolator = itp.RegularGridInterpolator(
                xyzcoord, self.bmap["Bx"], bounds_error=False, fill_value=0.0 )
            self.By_interpolator = itp.RegularGridInterpolator(
                xyzcoord, self.bmap["By"], bounds_error=False, fill_value=0.0 )
            self.Bz_interpolator = itp.RegularGridInterpolator(
                xyzcoord, self.bmap["Bz"], bounds_error=False, fill_value=0.0 )

        # ------------------------------------------------- #
        # --- [2] E-Field interpolator                  --- #
        # ------------------------------------------------- #
        if ( self.emap is not None ):
            rzcoord = ( self.emap["rAxis"], self.emap["zAxis"] )
            self.Er_interpolator = itp.RegularGridInterpolator(
                rzcoord, self.emap["Er"], bounds_error=False, fill_value=0.0 )
            self.Ez_interpolator = itp.RegularGridInterpolator(
                rzcoord, self.emap["Ez"], bounds_error=False, fill_value=0.0 )


    # ===================================================== #
    # === _evaluate_fields                              === #
    # ===================================================== #
    def _evaluate_fields( self, xp, yp, zp, tp=0.0 ):
        """ Evaluate E and B at particle positions.
        
        Args:
            xp, yp, zp (ndarray) : x-, y-, z- positions  [size = npart]
            tp         (ndarray) : time coordinate for RF modulation.
                                   Relative to reference particle. ( optional )
        Returns:
            Ex,Ey,Ez,Bx,By,Bz (ndarray) : 
        """
        cv    = 2.99792458e8

        # ------------------------------------------------- #
        # --- [1] initialization                        --- #
        # ------------------------------------------------- #
        npart = len( xp )
        Ex    = np.zeros( npart )
        Ey    = np.zeros( npart )
        Ez    = np.zeros( npart )
        Bx    = np.zeros( npart )
        By    = np.zeros( npart )
        Bz    = np.zeros( npart )

        # ------------------------------------------------- #
        # --- [2] B-Field                               --- #
        # ------------------------------------------------- #
        if ( self.Bx_interpolator is not None ):
            pts3  = np.column_stack( [xp, yp, zp] )
            Bx[:] = self.Bx_interpolator( pts3 )
            By[:] = self.By_interpolator( pts3 )
            Bz[:] = self.Bz_interpolator( pts3 )

        # ------------------------------------------------- #
        # --- [3] E-Field                               --- #
        # ------------------------------------------------- #
        if ( self.Er_interpolator is not None ):
            rp       = np.sqrt( xp**2 + yp**2 )
            pts2     = np.column_stack( [rp, zp] )
            phi      = np.deg2rad( self.phase ) + ( 2.0*np.pi*self.freq * tp/cv )
            phaseMod = np.cos( phi )

            Er       = self.Er_interpolator( pts2 ) * phaseMod
            Ez[:]    = self.Ez_interpolator( pts2 ) * phaseMod

            # conversion ::  Er => (Ex, Ey)
            mask     = ( rp > 0.0 )
            rpInv    = 1.0 / rp[mask]
            Ex[mask] = Er[mask] * xp[mask] * rpInv
            Ey[mask] = Er[mask] * yp[mask] * rpInv

        return( Ex,Ey,Ez, Bx,By,Bz )


    # ========================================================= #
    # ===  reference particle pusher from eb-field          === #
    # ========================================================= #
    def _push__refp_fromfield( self, refpart ):
        """ push reference particle using EB-map and Explicit Euler Method
        
        Args:
            refpart ( ImpactX.particle_container.refpart ) : reference particle info.
        """
        cv          = 2.99792458e8
        MeV         = 1.0e6
        # ------------------------------------------------- #
        # --- [1] ref_particle info.                    --- #
        # ------------------------------------------------- #
        ref_s_se    = refpart.s - refpart.sedge  # sedge :: s of the element's start point.
        q_sign      = refpart.charge_qe
        mass_MeV    = refpart.mass_MeV
        q_mc        = ( q_sign * cv ) / ( mass_MeV * MeV )
        gammaInv    = 1.0 / np.sqrt( 1.0 + refpart.px**2 + refpart.py**2 + refpart.pz**2 )
        betax       = refpart.px * gammaInv
        betay       = refpart.py * gammaInv
        betaz       = refpart.pz * gammaInv

        # ------------------------------------------------- #
        # --- [2] interpolate EB-fields                 --- #
        # ------------------------------------------------- #
        rx,ry,rs          = np.array( [refpart.x] ),np.array( [refpart.y] ),np.array( [ref_s_se] )
        Ex,Ey,Ez,Bx,By,Bz = self._evaluate_fields( rx,ry,rs,tp=0.0 )
        
        # ------------------------------------------------- #
        # --- [3] 1st-order Euler method integration    --- #
        # ------------------------------------------------- #
        ds_sliced = self.ds / self.nslice
        dt_sec    = ds_sliced / ( betaz * cv )
        
        Fx        = Ex[0] + cv * ( betay * Bz[0] - betaz * By[0] )
        Fy        = Ey[0] + cv * ( betaz * Bx[0] - betax * Bz[0] )
        Fz        = Ez[0] + cv * ( betax * By[0] - betay * Bx[0] )
        px_new    = refpart.px + q_mc * Fx * dt_sec
        py_new    = refpart.py + q_mc * Fy * dt_sec
        pz_new    = refpart.pz + q_mc * Fz * dt_sec
        gamma     = np.sqrt( 1.0 + px_new**2 + py_new**2 + pz_new**2 )
        pt_new    = -1.0 * gamma
        # gammaInv  =  1.0 / gamma       # not needed for 1st-order Euler
        # betax_new = px_new * gammaInv
        # betay_new = py_new * gammaInv
        # betaz_new = pz_new * gammaInv
        
        refpart.x   = refpart.x + cv * betax * dt_sec  # use old betax for 1st-order Euler
        refpart.y   = refpart.y + cv * betay * dt_sec
        refpart.z   = refpart.z + cv * betaz * dt_sec
        refpart.t   = refpart.t + cv *         dt_sec
        refpart.px  = px_new
        refpart.py  = py_new
        refpart.pz  = pz_new
        refpart.pt  = pt_new
        refpart.s   = refpart.s + ds_sliced


    # ========================================================= #
    # ===  beam particle pusher from eb-field               === #
    # ========================================================= #
    def _push__beam_fromfield( self, pc, refpart, ref_old ):
        """ push beam particles using EB-map and Explicit Euler Method
        
        Args:
            pc      ( ImpactX.particle_container )
            refpart ( ImpactX.particle_container.refpart ) :     reference particle info.
            ref_old ( dictionary )                         : old reference particle info.
        """
        cv          = 2.99792458e8
        MeV         = 1.e6
        # ------------------------------------------------- #
        # --- [1] ref_particle info.                    --- #
        # ------------------------------------------------- #
        q_sign      = refpart.charge_qe
        mass_MeV    = refpart.mass_MeV
        q_mc        = ( q_sign * cv ) / ( mass_MeV * MeV )
        
        ref_s_se    = ref_old["s"] - ref_old["sedge"]
        ref_bg_i    = np.sqrt( ref_old["px"]**2 + ref_old["py"]**2 + ref_old["pz"]**2 )
        ref_gamma_i = (-1.0) * ref_old["pt"]

        # ------------------------------------------------- #
        # --- [2] access to the real data of particles  --- #
        # ------------------------------------------------- #
        for lvl in range( pc.finest_level+1 ):
            for pti in impactx.ImpactXParIter( pc, level=lvl ):

                # ------------------------------------------------- #
                # --- [2-1] particle access                     --- #
                # ------------------------------------------------- #
                soa      = pti.soa()
                r_array  = soa.get_real_data()
                xp       = np.array( r_array[0], copy=False )
                yp       = np.array( r_array[1], copy=False )
                tp       = np.array( r_array[2], copy=False )
                px       = np.array( r_array[3], copy=False )
                py       = np.array( r_array[4], copy=False )
                pt       = np.array( r_array[5], copy=False )
                if (len(xp) == 0):
                    continue

                # ------------------------------------------------- #
                # --- [2-2] conversion to absolute coordinates  --- #
                # ------------------------------------------------- #
                xp_abs_i = ref_old["x"]  + xp
                yp_abs_i = ref_old["y"]  + yp
                tp_abs_i = ref_old["t"]  + tp
                px_abs_i = ref_old["px"] + ref_bg_i * px
                py_abs_i = ref_old["py"] + ref_bg_i * py
                
                gm_abs_i = ref_gamma_i - ref_bg_i * pt
                pz_abs_i = np.sqrt( gm_abs_i**2 - px_abs_i**2 - py_abs_i**2 - 1.0 )
                gammaInv = 1.0 / gm_abs_i
                betax    = px_abs_i * gammaInv
                betay    = py_abs_i * gammaInv
                betaz    = pz_abs_i * gammaInv
                sp_abs_i = ref_s_se - betaz * tp #  consiering betaz is needed. (opinion)
                # sp_abs_i = ref_s_se - tp 
                
                # ------------------------------------------------- #
                # --- [2-3] interpolate EB-fields               --- #
                # ------------------------------------------------- #
                Ex,Ey,Ez,Bx,By,Bz = self._evaluate_fields( xp_abs_i, yp_abs_i, sp_abs_i, tp=tp )
                
                # ------------------------------------------------- #
                # --- [2-4] 1st-order Euler method integration  --- #
                # ------------------------------------------------- #
                ds_sliced   = self.ds / self.nslice
                dt_sec      = ds_sliced / ( betaz * cv )

                Fx          = Ex + cv * ( betay * Bz - betaz * By )
                Fy          = Ey + cv * ( betaz * Bx - betax * Bz )
                Fz          = Ez + cv * ( betax * By - betay * Bx )
                px_abs_f    = px_abs_i + q_mc * Fx * dt_sec
                py_abs_f    = py_abs_i + q_mc * Fy * dt_sec
                pz_abs_f    = pz_abs_i + q_mc * Fz * dt_sec
                
                gm_abs_f    = np.sqrt( 1.0 + px_abs_f**2 + py_abs_f**2 + pz_abs_f**2 )
                pt_abs_f    = - gm_abs_f
                
                xp_abs_f    = xp_abs_i + cv * betax * dt_sec
                yp_abs_f    = yp_abs_i + cv * betay * dt_sec
                tp_abs_f    = tp_abs_i + cv *         dt_sec

                ref_bg_f    = np.sqrt( refpart.px**2 + refpart.py**2 + refpart.pz**2 )
                
                xp[:]       =     xp_abs_f - refpart.x
                yp[:]       =     yp_abs_f - refpart.y
                tp[:]       =     tp_abs_f - refpart.t
                px[:]       =   ( px_abs_f - refpart.px ) / ref_bg_f
                py[:]       =   ( py_abs_f - refpart.py ) / ref_bg_f
                pt[:]       =   ( pt_abs_f - refpart.pt ) / ref_bg_f
        

    # ========================================================= #
    # ===  total particle pusher from eb-field              === #
    # ========================================================= #
    def _push__fromfield( self, pc, step, period ):
        """ push beam particles using EB-map and Explicit Euler Method
        
        Args:
            pc      ( ImpactX.particle_container ) : particle_container
            step    ( int ) : required by programmable element
            period  ( ) : required by programmable element
        """
        refpart = pc.ref_particle()
        ref_old = { "x"  :refpart.x,  "y" :refpart.y,  "z" :refpart.z,  "t" :refpart.t,
                    "px" :refpart.px, "py":refpart.py, "pz":refpart.pz, "pt":refpart.pt,
                    "s"  :refpart.s,  "sedge":refpart.sedge }
        self._push__refp_fromfield( refpart )
        self._push__beam_fromfield( pc, refpart, ref_old )
                        

```


## main_impactx.py

```python
import os, sys, json5, time
import impactx
import numpy   as np
import pandas  as pd
import nk_toolkit.impactx.run_toolkit as rtk
import EBmapElement__ExplicitEuler    as ebm

# ========================================================= #
# ===  impactX tracking file                            === #
# ========================================================= #

def main_impactx():

    amu        = 931.494              # [MeV]
    bfieldfile = "../dat/bfield.dat"
    efieldfile = "../dat/efield.dat"
    
    # ------------------------------------------------- #
    # --- [1]  load parameters                      --- #
    # ------------------------------------------------- #
    paramsFile = "../dat/parameters.json"
    with open( paramsFile, "r" ) as f:
        params = json5.load( f )

    # ------------------------------------------------- #
    # --- [2]  initialization                       --- #
    # ------------------------------------------------- #
    ts  = time.perf_counter()
    sim = impactx.ImpactX()

    sim.max_level         = params["sim.max_level"]
    sim.n_cell            = params["sim.n_cell"]
    sim.blocking_factor   = params["sim.blocking_factor"]
    
    sim.particle_shape                    = 2
    sim.slice_step_diagnostics            = True
    sim.particle_lost_diagnostics_backend = ".h5"
    sim.space_charge                      = params["mode.space_charge"]
    sim.poisson_solver                    = "fft"       # fft or multigrid ( fft(IGF) is only outer side )
    sim.dynamic_size                      = True        # True
    sim.prob_relative                     = [1.2,1.1]   # ptcl's min-max * prob_relative = pic's sim-size
    #                                                   # ( 1.2-1.1 for fft, >3.0 for multigrid )
    sim.init_grids()
    
    # ------------------------------------------------- #
    # --- [3] reference particle                    --- #
    # ------------------------------------------------- #
    Ek0 = params["beam.Ek.MeV/u"] * params["beam.u.nucleon"]
    Em0 = params["beam.mass.amu"] * amu
    ref = sim.particle_container().ref_particle()
    ref.set_charge_qe     ( params["beam.charge.qe"] )
    ref.set_mass_MeV      ( Em0 )
    ref.set_kin_energy_MeV( Ek0 )
    
    # ------------------------------------------------- #
    # --- [4] distribution                          --- #
    # ------------------------------------------------- #
    distri = rtk.set__waterbag_distribution( alpha   =np.array( params["beam.twiss.alpha"]    ), \
                                             beta    =np.array( params["beam.twiss.beta" ]    ), \
                                             eps_geom=np.array( params["beam.emittance.geom"] ), \
                                             mm_mrad=True, full_emittance=False )
    sim.add_particles( params["beam.charge.C"], distri, int( params["beam.nparticles"]) )

    # pc        = sim.particle_container()
    # particles = [ [ 0,0,0, 0,0,-1.e-6 ],
    #               [ 0,0,0, 0,0,+1.e-6 ] ]
    # rtk.set__manualReferenceParticle( particle_container=pc, particles=particles )
    
    # ------------------------------------------------- #
    # --- [5] set lattice                           --- #
    # ------------------------------------------------- #
    beamline     = []
    bpm          = impactx.elements.BeamMonitor( "bpm", backend="h5" )
    dr1          = impactx.elements.ExactDrift( name="dr1", ds=0.1, \
                                                aperture_x=0.1, aperture_y=0.1, nslice=1 )
    dr2          = impactx.elements.ExactDrift( name="dr2", ds=0.2, \
                                                aperture_x=0.1, aperture_y=0.1, nslice=4 )
    acc0         = ebm.EBmapElement__ExplicitEuler( ds=0.2, nslice=4, name="acc0", \
                                                    freq=0.0, phase=0.0, \
                                                    bfieldfile=bfieldfile, bfactor=0.0, \
                                                    efieldfile=efieldfile, efactor=0.0,  )
    acc1         = ebm.EBmapElement__ExplicitEuler( ds=0.2, nslice=4, name="acc1", \
                                                    freq=0.0, phase=0.0, \
                                                    bfieldfile=bfieldfile, bfactor=1.0, \
                                                    efieldfile=efieldfile, efactor=1.0,  )

    cv           = 2.99792458e8
    qe           = 1.602e-19
    MeV          = 1.e6
    ez_value     = qe * 1.0e6 / ( Em0 * MeV * qe      )
    bz_value     = qe * 1.0   / ( Em0 * MeV * qe / cv )
    cha          = impactx.elements.ChrAcc( name="cha", ds=0.2, nslice=4, \
                                            ez=ez_value, bz=bz_value )
    
    beamline1    = [ bpm, dr1, bpm,  dr2, bpm, dr1, bpm ]
    beamline2    = [ bpm, dr1, bpm,  cha, bpm, dr1, bpm ]
    beamline3    = [ bpm, dr1, bpm, acc0, bpm, dr1, bpm ]
    beamline4    = [ bpm, dr1, bpm, acc1, bpm, dr1, bpm ]

    sim.lattice.extend( beamline4 )
    
    # ------------------------------------------------- #
    # --- [6] tracking                              --- #
    # ------------------------------------------------- #
    sim.track_particles()
    sim.finalize()
    te  = time.perf_counter()
    print( "\n Elapsed time ::: {:10.5e} (s)\n".format( te-ts ) )

    # ------------------------------------------------- #
    # --- [7] save in a file                        --- #
    # ------------------------------------------------- #
    rtk.save__run_records( params=params, recoFile="diags/records.json" )
    # rtk.save__latticeStructure( beamlineFile=beamlineFile, nUse=params["sim.nUse.elements"], \
    #                             outFile="diags/lattice.csv" )
    
    

# ========================================================= #
# ===   Execution of Pragram                            === #
# ========================================================= #

if ( __name__=="__main__" ):
    main_impactx()
    

```

## generate__sampleField.py

```python

import os
import numpy as np


# ========================================================= #
# ===  generate__sample_bfield                          === #
# ========================================================= #
def generate__sample_bfield(
    filename="dat/bfield.dat",
    xlim=(-0.02, 0.02),
    ylim=(-0.02, 0.02),
    zlim=( 0.00, 0.10),
    nx=5,
    ny=5,
    nz=11,
    bz_const=1.0
):
    """
    bfield.dat format:
      x, y, z, Bx, By, Bz

    Test field:
      Bx = 0
      By = 0
      Bz = const.
    """

    xAxis = np.linspace(xlim[0], xlim[1], nx)
    yAxis = np.linspace(ylim[0], ylim[1], ny)
    zAxis = np.linspace(zlim[0], zlim[1], nz)

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w") as f:
        for x in xAxis:
            for y in yAxis:
                for z in zAxis:
                    bx = 0.0
                    by = 0.0
                    bz = bz_const
                    f.write(f"{x: .8e} {y: .8e} {z: .8e} {bx: .8e} {by: .8e} {bz: .8e}\n")

    print(f"[ok] wrote {filename}")
    print(f"     grid = ({nx}, {ny}, {nz}),  Bz = {bz_const} [T]")


# ========================================================= #
# ===  generate__sample_efield                          === #
# ========================================================= #
def generate__sample_efield(
    filename="dat/efield.dat",
    rlim=(0.00, 0.02),
    zlim=(0.00, 0.20),
    nr=5,
    nz=11,
    ez_const=5.e6
):
    """
    efield.dat format:
      r, z, Er, Ez

    Test field:
      Er = 0
      Ez = const.
    """

    rAxis = np.linspace(rlim[0], rlim[1], nr)
    zAxis = np.linspace(zlim[0], zlim[1], nz)

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w") as f:
        for r in rAxis:
            for z in zAxis:
                er = 0.0
                ez = ez_const
                f.write(f"{r: .8e} {z: .8e} {er: .8e} {ez: .8e}\n")

    print(f"[ok] wrote {filename}")
    print(f"     grid = ({nr}, {nz}),  Ez = {ez_const} [V/m]")


# ========================================================= #
# ===  main                                             === #
# ========================================================= #
if __name__ == "__main__":

    generate__sample_bfield(
        filename="dat/bfield.dat",
        xlim=(-0.20, 0.20),
        ylim=(-0.20, 0.20),
        zlim=(-0.20, 0.20),
        nx=5,
        ny=5,
        nz=11,
        bz_const=1.0          # 1.0 T
    )

    generate__sample_efield(
        filename="dat/efield.dat",
        rlim=( 0.00, 0.20),
        zlim=(-0.20, 0.20),
        nr=5,
        nz=11,
        ez_const=1.00e6       # 1 MV/m
    )


```

# 検証

## デバグと１粒子検証は、逐次実施

- 実行可能であることを確認。

## E=0, B=0 でのドリフト動作の確認

1. ds=0.2 m のExactDrift でトラッキング
2. E=0, B=0 の電磁場マップをひろうビームエレメントでトラッキング

	- 1 - 2 を比較して、==ドリフト== があっていることを確認する。


### main_impactx.py内の選択

```python
    beamline1    = [ bpm, dr1, bpm,  dr2, bpm, dr1, bpm ]
    beamline2    = [ bpm, dr1, bpm, acc0, bpm, dr1, bpm ]
    beamline3    = [ bpm, dr1, bpm,  cha, bpm, dr1, bpm ]
    beamline4    = [ bpm, dr1, bpm, acc1, bpm, dr1, bpm ]

    sim.lattice.extend( beamline1 )  # <- ここで選択
```

### 比較結果

![[drift_vs_E0B0.png]]

- 左列： ExactDrift 要素
- 右列： EBmapElement__ExplicitEuler要素 ( E=0, B=0 ：ドリフト)

	- ==一致== を確認


## E=1 MV/m, B=1 T の電磁場マップ中での挙動の確認

### 比較結果

![[ChrAcc_vs_E1B1.png]]

- 左列： ChrAcc 要素
- 右列： EBmapElement__ExplicitEuler要素 ( E=1 MV/m, B=1 T )

	- かなり挙動が異なる。 (特に横方向拡がり：　$\sigma_{x}, \, \sigma_{y}$ , $\epsilon_x$, $\epsilon_y$)
	- 不安定・低精度なEuler陽解法で nslice=4であることが問題点？
		==→== nslice = 100 等で試す。

### デバグログ

- nslice = 100 等、nsliceを増やすと、電磁場マップ要素の端部で ==不連続な挙動==
- 下記の訂正 (内挿位置をref_particle 位置にする)

```python
   sp_abs_i = np.repeat( [ ref_s_se ], len(tp), axis=0 )
   # sp_abs_i = ref_s_se - betaz * tp
```

- １行目が正しいと考えている ( 内挿位置情報はref_particle 位置 )
- ２行目：各粒子の位置を再構成して内挿だと、マップ領域外(E=0, B=0等)にはいる粒子あり
	- 境界域で変な挙動をする　（==不連続==）
- 一見、物理的におかしいが、軌道sでdsごと進めて積分するので、評価（積分）ポイントをds/nsliceごとにおいているだけで、物理情報を拾う、内挿位置はref_particle 位置でよい。
	- 粒子ごとのいちばらつきは、t変数が、微小時間、早い・遅いで管理する (dt積分とds積分で積分の進め方の考え方が異なっている。)
	- ImpactXはds積分のコードなので、こちらでよいはず。

#### ただし問題点として粒子サイズのndarrayを定義していることに注意

- 粒子数を上げたときに、間違いなく、メモリが足りなくなる。
	- 粒子数が上げた際は、chunk毎の処理化を別途、導入することになるはず。
	- 当面の原理実証では、一旦、無視


## ChrAccとの差異の確認： nslice 依存性

### nslice = 4, 100 の比較

![[nslice4_100.png]]

* 明確に、nslice = 4 → 100で、エミッタンスは減少、ChrAccに近寄った。
- ただし、ChrAccとは一致というわけではない。==→== nsliceが足りてなさそうか。

### nslice=500 とChrAccとの比較

![[nslice500_ChrAcc.png]]

- ds=4 からすると、近づいてはいるが、ChrAccとの差はある。

|      | Explicit Euler | ChrAcc    |
| ---- | -------------- | --------- |
| 計算原理 | 積分             | 行列（線形光学）  |
| 精度   | 1次精度           | -         |
| 特徴   | 不安定            | シンプレクティック |

- なので、Explicit Eulerでは、厳しい面があると考えられる
	-  簡易な積分計算方法として、Bunemann-Boris, RK2を用いるなどで対策する。

