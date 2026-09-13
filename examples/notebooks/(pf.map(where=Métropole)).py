# coding: utf-8
import sys
sys.path.insert(0, "/Users/dadoun/Programs/Python/coa-project/pyvoa")
import pyvoa.front as pf
pf.setwhom('spf',reload=False)
pf.setvis('matplotlib')
pf.map(where='Métropole')
pf.setwhom('spf',reload=False)
pf.setvis('bokeh')
pf.map(where='Métropole')
