
# ImpactXへの実装案

1. 実マップを読み込んで計算する独自ルーチン (C++コアのコード) を開発する
	- C++直接いじる開発は大変
	  
2. 標準機能 ( 電場：shortRF or RFcavity, 磁場：Quad or solenoid )を使用して、分割して等価なビームエレメントをつくる ( e.g. DTL = shortRF1 + solenoid + shortRF2 etc. ）
	- 構築方法を考える必要あり。（Strang Splitting を適用か？ =  Thin - Thick - Thin で ）
	- Thin elementであり、実磁場マップからは乖離しうる。近似が入る。

3. RFcavity + Soft Solenoid： dsが重複できないが、Strang Splittingを使用して、
	- RFcavity (ds/2 ) + SoftSolenoid(ds) + RFcavity(ds/2) として計算 (Thick要素)。
	- ただし、ds/2 + ds + ds/2 なので、2ds になる問題あり。
	
4.  ChrAccを用いて、Bz=const., Ez=const.の電磁場でトラッキングする
	- 最も簡便。
	- 実電磁場に対して、忠実ではない。その後の拡張も難しい ( 検証用 or 1st用 )。

5.  Programmable 要素（Pythonを使用した簡易コーディング要素）を使用してマップからの内挿ルーチンを作成する
	- Programmable 要素の詳細を勉強する必要あり。

6. TransferMatrixを計算し、kickをマトリックスとして記述
	- pre-defined なマップのみ記載可能（ビーム情報に応じた二次以上の効果は無視）


# 実装案の整理

- 実装案のpros/consによる整理は下記
- 評価軸は、「実装の容易性」「物理の忠実性」「保守・発展性」の３軸

| 実装案                     | 実装の容易性 | 物理の忠実性 | 保守・発展性 | コメント                                                                        |
| :---------------------- | :----: | :----: | :----: | :-------------------------------------------------------------------------- |
| 1. 実マップ読込ルーチン           |   ✗    |   ◎    |   ○    | - 最も本格的。<br>- C++ 実装をつくる。<br>- 実マップを直接的に扱う。<br>- 初期実装・保守コストが大。              |
| 2. shortRF+SoftSolenoid |   ○    |   △    |   △    | - 薄レンズ電場+ソレノイドで近似<br>- Strang Splitting(Thin/Thick/Thin)<br>- 構築方法に恣意性が残りそう |
| 3.RFcavity+SoftSolenoid |   △    |   △    |   △    | - Thick / Thick /Thick で Strang Splitting<br>- すべて電場と磁場の重畳が難                |
| 4. ChrAcc 要素            |   ◎    |   ✗    |   △    | - Bz, Ez = const. で近似 <br>- 簡便                                              |
| 5. Programmable要素       |   ○    |   ○    |   ◎    | - C++ではなくpythonで要素を作成<br>- 実電磁場を読める可能性あり。<br>- 動作や制約の確認が必要。                 |
| 6. LinearMap要素          |   ○    |   ✗    |   △    | - 線形近似としては有効だが、非線形・位相依存・高次効果は落ちる。                                           |

## 優先順位

$$
5 \rightarrow 4 \rightarrow 2 \rightarrow 1
$$

- Programmable 要素の可否検討
	- 問題ない → Programmable 要素 + ChrAcc要素で比較検証
	- 問題あり → 2.shortRF+SoftSolenoid + ChrAcc要素で比較検証
	
- もしも、精度検証の結果がよろしくない場合、（Track v.s. ImpactX ( ChrAcc/others )）
	- C++実装を頑張る。


# Programmable 要素について

## 概要  
  
Python インタフェースから簡易に粒子への作用を定義する光学要素を定義する。  
  
- `main_impactx.py` に直接、
`(x, y, z, px, py, pz)` の更新関数 (push)を直接記載する  
  
## 基本的な使用の方法  
  
1. `elements.Programmable()` を宣言またはクラス継承
2. `name`, `ds`, `nslice` を与える（引数 or 代入）  
3. `push` の更新ルーチンを関数として定義  
4. 上記 (1) のクラスに (3) の関数を hook  
5. `lattice` に (1) のクラスを含める  
  
## サンプルコード  
  
- FODO cell（Programmable Element）  (Impactx 公式)
- 15 stage Laser-Plasma Accelerator Surrogate  (Impactx 公式)
  
## 制約・懸念事項  
  
- OpenMP 化に関して，デフォルトでは不可  
- 多粒子 (1e6以上等)での 高速計算が可能かどうかが未知数  (もしかすると激重)
  
## 実装の構成案  
  
- 以下をもつライブラリを定義
	- 実磁場／実電場のファイル名指定からの読込ルーチン
	- 粒子位置を反映して、磁場・電場の内挿ルーチン  
	- 内挿した (E,B)を反映した push ルーチン  
	
-  上記３ルーチンは、impactx.elements.Programmable() のクラス継承で定義

# Appendix.   Programmable Element FODO cell の例

```python
#!/usr/bin/env python3
#
# Copyright 2022-2023 ImpactX contributors
# Authors: Axel Huebl, Chad Mitchell
# License: BSD-3-Clause-LBNL
#
# -*- coding: utf-8 -*-


from impactx import ImpactX, distribution, elements

sim = ImpactX()

# set numerical parameters and IO control
sim.space_charge = False
# sim.diagnostics = False  # benchmarking
sim.slice_step_diagnostics = True

# domain decomposition & space charge mesh
sim.init_grids()

# load a 2 GeV electron beam with an initial
# unnormalized rms emittance of 2 nm
kin_energy_MeV = 2.0e3  # reference energy
bunch_charge_C = 1.0e-9  # used with space charge
npart = 10000  # number of macro particles

#   reference particle
ref = sim.particle_container().ref_particle()
ref.set_charge_qe(-1.0).set_mass_MeV(0.510998950).set_kin_energy_MeV(kin_energy_MeV)

#   particle bunch
distr = distribution.Waterbag(
    lambdaX=3.9984884770e-5,
    lambdaY=3.9984884770e-5,
    lambdaT=1.0e-3,
    lambdaPx=2.6623538760e-5,
    lambdaPy=2.6623538760e-5,
    lambdaPt=2.0e-3,
    muxpx=-0.846574929020762,
    muypy=0.846574929020762,
    mutpt=0.0,
)
sim.add_particles(bunch_charge_C, distr, npart)

# number of slices per ds in each lattice element
ns = 25


# build a custom, Pythonic beam optical element
def my_drift(pge, pti, refpart):
    """This pushes the beam particles as a drift.

    Relative to the reference particle.

    :param pti: particle iterator for the current tile or box
    :param refpart: the reference particle
    """
    # access particle attributes
    soa = pti.soa().to_xp()  # automatic: NumPy (CPU) or CuPy (GPU)

    x = soa.real["position_x"]
    y = soa.real["position_y"]
    t = soa.real["position_t"]
    px = soa.real["momentum_x"]
    py = soa.real["momentum_y"]
    pt = soa.real["momentum_t"]

    # length of the current slice
    slice_ds = pge.ds / pge.nslice

    # access reference particle values to find beta*gamma^2
    pt_ref = refpart.pt
    betgam2 = pt_ref**2 - 1.0

    # advance position and momentum (drift)
    x[:] += slice_ds * px[:]
    y[:] += slice_ds * py[:]
    t[:] += (slice_ds / betgam2) * pt[:]


def my_ref_drift(pge, refpart):
    """This pushes the reference particle.

    :param refpart: reference particle
    """
    #  assign input reference particle values
    x = refpart.x
    px = refpart.px
    y = refpart.y
    py = refpart.py
    z = refpart.z
    pz = refpart.pz
    t = refpart.t
    pt = refpart.pt
    s = refpart.s

    # length of the current slice
    slice_ds = pge.ds / pge.nslice

    # assign intermediate parameter
    step = slice_ds / (pt**2 - 1.0) ** 0.5

    # advance position and momentum (drift)
    refpart.x = x + step * px
    refpart.y = y + step * py
    refpart.z = z + step * pz
    refpart.t = t - step * pt

    # advance integrated path length
    refpart.s = s + slice_ds


pge1 = elements.Programmable(name="d1")
pge1.nslice = ns
pge1.beam_particles = lambda pti, refpart: my_drift(pge1, pti, refpart)
pge1.ref_particle = lambda refpart: my_ref_drift(pge1, refpart)
pge1.ds = 0.25

# attention: assignment is a reference for pge2 = pge1

pge2 = elements.Programmable(name="d2")
pge2.nslice = ns
pge2.beam_particles = lambda pti, refpart: my_drift(pge2, pti, refpart)
pge2.ref_particle = lambda refpart: my_ref_drift(pge2, refpart)
pge2.ds = 0.5

# add beam diagnostics
monitor = elements.BeamMonitor("monitor", backend="h5")

# design the accelerator lattice
fodo = [
    monitor,
    pge1,  # equivalent to elements.Drift("d1", ds=0.25, nslice=ns)
    monitor,
    elements.Quad(name="q1", ds=1.0, k=1.0, nslice=ns),
    monitor,
    pge2,  # equivalent to elements.Drift("d2", ds=0.5, nslice=ns)
    monitor,
    elements.Quad(name="q2", ds=1.0, k=-1.0, nslice=ns),
    monitor,
    pge1,  # equivalent to elements.Drift("d1", ds=0.25, nslice=ns)
    monitor,
]
# assign a fodo segment
sim.lattice.extend(fodo)

# run simulation
sim.track_particles()

# clean shutdown
sim.finalize()

```