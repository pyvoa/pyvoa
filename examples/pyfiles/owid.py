import pyvoa.front as pv
import pyvoa.tools as pt
import matplotlib
matplotlib.use('Agg')

pt.set_verbose_mode(2)
def test():
    pv.setwhom('owid',reload=False)
    pv.setvis(vis='matplotlib')
    pv.map(where='Europe')
    return pv

pl = test()
pl.savefig('mapspf.png')
