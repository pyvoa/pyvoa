import pyvoa.front as pv
import matplotlib
matplotlib.use('Agg')

def test():
    pv.setwhom('owid',reload=False)
    pv.setvisu(vis='matplotlib')
    pv.map(where='Europe')
    return pv

pl = test()
pl.savefig('mapspf.png')
