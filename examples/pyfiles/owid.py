import sys

sys.path.append('../..')

import matplotlib

import pyvoa.front as pf

matplotlib.use('Agg')

def test():
    pf.setwhom('owid',reload=False)
    pf.setvis(vis='matplotlib')
    pf.map(where='Europe')
    return pf

pl = test()
pl.savefig('mapowid.png')
