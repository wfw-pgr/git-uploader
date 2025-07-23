nslice   = 1
monitor  = impactx.elements.BeamMonitor( "monitor", backend="h5" )
dr1      = impactx.elements.ExactDrift( name="dr1", ds=0.25, nslice=nslice )
dr2      = impactx.elements.ExactDrift( name="dr2", ds=0.50, nslice=nslice )
qf1      = impactx.elements.ExactQuad(  name="qf1", ds=1.0, k=+1.0, int_order=4, \
                                        nslice=nslice, mapsteps=4 )
qd1      = impactx.elements.ExactQuad(  name="qd1", ds=1.0, k=-1.0, int_order=4, \
                                        nslice=nslice, mapsteps=4 )
beamline = [
    monitor,
    dr1,
    monitor, 
    qf1,
    monitor,
    dr2,
    monitor,
    qd1, 
    monitor,
    dr1,
    monitor, 
]
