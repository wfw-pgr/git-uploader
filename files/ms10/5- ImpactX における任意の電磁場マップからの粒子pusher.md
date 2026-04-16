
# 目的

- ImpactX の `Programmable` 要素を用いて、任意の電磁場マップを読込み、粒子をpushするルーチンを構築する。


# 実装
## 電磁場マップの想定

- 磁場：3 次元直交座標マップ  $(B_x, B_y, B_z)$
- 電場：RZ２次元の軸対称マップ  $(E_r,E_z)$

## 取組概要

### pusherクラスの概要

- `impactx.elements.Programmable` を継承したクラス `particlepusher__fromfield` を作成

	- 以下がメンバ関数
		- 電磁場マップファイルの読み込み
		- 補間関数 (interpolator)の生成
		- 粒子位置での場の評価 
		- その場を用いた粒子 push

### pusherクラスの入力

- `ds`
- `name`
- `nslice`
- `bfieldfile`
- `efieldfile`
- `bfactor`
- `efactor`
- `phase`
    

### 想定の実装工程流れ

1. `Programmable` 継承クラスを定義する。
2.  ImpactX でのテストルーチン生成、組み込み、最小粒子数でテスト
3.  1段のTRACKの結果と比較 


# コード草案

```python
import numpy as np
from scipy.interpolate import RegularGridInterpolator

# ========================================================= #
# ===  particlepusher__fromfield                        === #
# ========================================================= #
#
#  Assumption:
#    - B-field file stores 3D Cartesian field:
#         columns = x, y, z, Bx, By, Bz
#
#    - E-field file stores axisymmetric 2D field:
#         columns = r, z, Er, Ez
#
#    - Units, normalization, and particle accessors
#      must be adjusted to actual ImpactX conventions.
#
# --------------------------------------------------------- #

class particlepusher__fromfield( impactx.elements.Programmable ):

    # ===================================================== #
    # ===  __init__                                     === #
    # ===================================================== #
    def __init__( self,
                  ds=0.0,
                  name="particlepusher__fromfield",
                  nslice=1,
                  bfieldfile=None,
                  efieldfile=None,
                  bfactor=1.0,
                  efactor=1.0,
                  phase=0.0 ):

        super().__init__( ds=ds, name=name, nslice=
                          nslice )

        self.ds         = ds
        self.name       = name
        self.nslice     = nslice

        self.bfieldfile = bfieldfile
        self.efieldfile = efieldfile

        self.bfactor    = float( bfactor )
        self.efactor    = float( efactor )
        self.phase      = float( phase )

        # containers for field maps / interpolators
        self.bmap       = None
        self.emap       = None

        self.binterp_x  = None
        self.binterp_y  = None
        self.binterp_z  = None

        self.einterp_r  = None
        self.einterp_z  = None

        # load field data and prepare interpolators
        self.load__ebfieldfile()
        self.interpolate__ebfieldfile()

        # assign programmable push
        self.push = self.push__fromfield


    # ===================================================== #
    # === load__ebfieldfile                             === #
    # ===================================================== #
    def load__ebfieldfile(self):
        """
        Load magnetic/electric field maps from files.

        Expected formats
        ----------------
        bfieldfile:
            columns = x, y, z, Bx, By, Bz

        efieldfile:
            columns = r, z, Er, Ez
        """

        # ----------------------------- #
        # --- load B-field          --- #
        # ----------------------------- #
        if self.bfieldfile is not None:
            bdat = np.loadtxt( self.bfieldfile )

            if ( bdat.shape[1] < 6 ):
                raise ValueError( "[ERROR] bfieldfile must have at least 6 columns: x, y, z, Bx, By, Bz" )
            
            xp_  = bdat[:,0]
            yp_  = bdat[:,1]
            zp_  = bdat[:,2]
            bx_  = bdat[:,3] * self.bfactor
            by_  = bdat[:,4] * self.bfactor
            bz_  = bdat[:,5] * self.bfactor

            xAxis = np.unique( xp_ )
            yAxis = np.unique( yp_ )
            zAxis = np.unique( zp_ )

            nx, ny, nz = len(xAxis), len(yAxis), len(zAxis)

            if nx * ny * nz != len(bdat):
                raise ValueError( "[ERROR] B-field map size is inconsistent with structured grid." )

            Bx = bx_.reshape( (nx, ny, nz), order="C" )
            By = by_.reshape( (nx, ny, nz), order="C" )
            Bz = bz_.reshape( (nx, ny, nz), order="C" )

            self.bmap = { "xAxis": xAxis, "yAxis": yAxis, "zAxis": zAxis,
                          "Bx"   : Bx   , "By"   : By   ,"Bz"    : Bz, }

        # ----------------------------- #
        # --- load E-field          --- #
        # ----------------------------- #
        if self.efieldfile is not None:
            edat = np.loadtxt( self.efieldfile )

            if edat.shape[1] < 4:
                raise ValueError( "[ERROR] efieldfile must have at least 4 columns: r, z, Er, Ez" )

            r_     = edat[:,0]
            z_     = edat[:,1]
            er_    = edat[:,2] * self.efactor
            ez_    = edat[:,3] * self.efactor
            rAxis  = np.unique( r_ )
            zAxis  = np.unique( z_ )
            nr, nz = len(rAxis), len(zAxis)

            if nr * nz != len(edat):
                raise ValueError( "[ERROR] E-field map size is inconsistent with structured (r,z) grid." )

            Er = er_.reshape( (nr, nz), order="C" )
            Ez = ez_.reshape( (nr, nz), order="C" )

            self.emap = { "rAxis": rAxis, "zAxis": zAxis, "Er": Er, "Ez": Ez }


    # ===================================================== #
    # interpolate__ebfieldfile
    # ===================================================== #
    def interpolate__ebfieldfile(self):
        """
        Construct interpolators for B(x,y,z) and E(r,z).
        """

        # ----------------------------- #
        # --- B-field interpolator  --- #
        # ----------------------------- #
        if self.bmap is not None:
            self.binterp_x = RegularGridInterpolator(
                ( self.bmap["xAxis"], self.bmap["yAxis"], self.bmap["zAxis"] ),
                self.bmap["Bx"], bounds_error=False, fill_value=0.0 )
            self.binterp_y = RegularGridInterpolator(
                ( self.bmap["xAxis"], self.bmap["yAxis"], self.bmap["zAxis"] ),
                self.bmap["By"], bounds_error=False, fill_value=0.0 )
            self.binterp_z = RegularGridInterpolator(
                ( self.bmap["xAxis"], self.bmap["yAxis"], self.bmap["zAxis"] ),
                self.bmap["Bz"], bounds_error=False, fill_value=0.0 )

        # ----------------------------- #
        # --- E-field interpolator  --- #
        # ----------------------------- #
        if self.emap is not None:
            self.einterp_r = RegularGridInterpolator(
                ( self.emap["rAxis"], self.emap["zAxis"] ),
                self.emap["Er"], bounds_error=False, fill_value=0.0 )
            self.einterp_z = RegularGridInterpolator(
                ( self.emap["rAxis"], self.emap["zAxis"] ),
                self.emap["Ez"], bounds_error=False, fill_value=0.0 )


    # ===================================================== #
    # === _evaluate_fields                              === #
    # ===================================================== #
    def _evaluate_fields( self, xp, yp, zp, tp=None ):
        """
        Evaluate E and B at particle positions.

        Parameters
        ----------
        xp, yp, zp : ndarray
            Particle coordinates.
        tp: Time coordinate for RF phase application if needed.

        Returns
        -------
        Ex, Ey, Ez, Bx, By, Bz : ndarray
        """

        npart = len(xp)

        Ex = np.zeros( npart )
        Ey = np.zeros( npart )
        Ez = np.zeros( npart )
        Bx = np.zeros( npart )
        By = np.zeros( npart )
        Bz = np.zeros( npart )

        # ----------------------------- #
        # --- magnetic field        --- #
        # ----------------------------- #
        if self.binterp_x is not None:
            pts3  = np.column_stack( [xp, yp, zp] )
            Bx[:] = self.binterp_x( pts3 )
            By[:] = self.binterp_y( pts3 )
            Bz[:] = self.binterp_z( pts3 )

        # ----------------------------- #
        # --- electric field        --- #
        # ----------------------------- #
        if self.einterp_r is not None:
            rp           = np.sqrt( xp*xp + yp*yp )
            pts2         = np.column_stack( [rp, zp] )
            phase_factor = np.cos( self.phase )

            # RF phase factor
            #
            # Minimal draft:
            #   E -> E * cos(phase)
            #
            # If actual time dependence is needed:
            #   E -> E * cos(omega*t + phase)
            #
            
            Er  = self.einterp_r( pts2 ) * phase_factor
            Ez_ = self.einterp_z( pts2 ) * phase_factor

            # axisymmetric field: convert (Er, Et=0) -> (Ex, Ey)
            mask     = ( rp > 0.0 )
            Ex[mask] = Er[mask] * xp[mask] / rp[mask]
            Ey[mask] = Er[mask] * yp[mask] / rp[mask]
            Ez[:]    = Ez_[:]

        return( Ex,Ey,Ez, Bx,By,Bz )


    # ===================================================== #
    # === push__fromfield                               === #
    # ===================================================== #
    def push__fromfield( self, pc, step=0 ):
        """
        Push particles through ds using external field maps.
        
        NOTE:
        -----
        This is a draft structure.
        The actual particle container API in ImpactX must be matched here.

        Expected workflow:
          1. get particle coordinates and momenta
          2. evaluate E/B
          3. apply Lorentz-force push
          4. write back updated coordinates/momenta
        """

        # ------------------------------------------------- #
        # --- [1] access particle arrays                --- #
        # ------------------------------------------------- #
        xp  = pc.x
        yp  = pc.y
        zp  = pc.z
        px  = pc.px
        py  = pc.py
        pz  = pc.pz

        # optional time coordinate if available
        tp  = getattr( pc, "t", None )

        # charge/mass must follow ImpactX unit conventions
        qp  = pc.q
        mp  = pc.m

        # ------------------------------------------------- #
        # --- [2] slicing / substepping                 --- #
        # ------------------------------------------------- #
        ds_slice = self.ds / self.nslice
        
        for islice in range( self.nslice ):

            # ----------------------------------------- #
            # --- [2-1] field evaluation            --- #
            # ----------------------------------------- #
            Ex, Ey, Ez, Bx, By, Bz = self._evaluate_fields( xp, yp, zp, tp=tp )

            # ----------------------------------------- #
            # --- [2-2] compute velocity            --- #
            # ----------------------------------------- #
            #
            # Draft relativistic conversion:
            #   p = gamma m v
            #   v = p / (gamma m)
            #
            # Here px,py,pz are assumed physical momenta.
            # If ImpactX uses normalized momenta, replace accordingly.
            #
            p2     = px*px + py*py + pz*pz
            gamma  = np.sqrt( 1.0 + p2 / (mp**2) )
            vx     = px / (gamma*mp)
            vy     = py / (gamma*mp)
            vz     = pz / (gamma*mp)

            # ----------------------------------------- #
            # --- [2-3] Lorentz force               --- #
            # ----------------------------------------- #
            #
            # dp/dt = q ( E + v x B )
            #
            Fx = qp * ( Ex + (vy*Bz - vz*By) )
            Fy = qp * ( Ey + (vz*Bx - vx*Bz) )
            Fz = qp * ( Ez + (vx*By - vy*Bx) )

            # ----------------------------------------- #
            # --- [2-4] convert ds to dt            --- #
            # ----------------------------------------- #
            #
            # Minimal draft:
            #   dt = ds / vz
            #
            # Need careful handling for low/negative vz.
            #
            vz_safe = np.where( np.abs(vz) > 1.0e-30, vz, 1.0e-30 )
            dt      = ds_slice / vz_safe

            # ----------------------------------------- #
            # --- [2-5] kick-drift (simple draft)   --- #
            # ----------------------------------------- #
            px[:] = px[:] + Fx[:] * dt[:]
            py[:] = py[:] + Fy[:] * dt[:]
            pz[:] = pz[:] + Fz[:] * dt[:]

            # recompute velocity after kick
            p2     = px*px + py*py + pz*pz
            gamma  = np.sqrt( 1.0 + p2 / ( mp**2 ) )
            vx     = px / ( gamma*mp )
            vy     = py / ( gamma*mp )
            vz     = pz / ( gamma*mp )

            xp[:] = xp[:] + vx[:] * dt[:]
            yp[:] = yp[:] + vy[:] * dt[:]
            zp[:] = zp[:] + vz[:] * dt[:]

            if tp is not None:
                tp[:] = tp[:] + dt[:]

        # ------------------------------------------------- #
        # --- [3] write back if needed                   --- #
        # ------------------------------------------------- #
        #
        # If pc arrays are views, no explicit write-back is needed.
        # Otherwise, assign them here.
        #
        pc.x  = xp
        pc.y  = yp
        pc.z  = zp
        pc.px = px
        pc.py = py
        pc.pz = pz

        if ( tp is not None ):
            pc.t = tp

```

# 残件メモ

- ランテスト
- 