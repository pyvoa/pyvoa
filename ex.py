import pyvoa.front as pv
pv.setwhom('owid',reload=False)
pv.setvis('matplotlib')

#pv.map(which='total_cases',what='current',option='nonneg')
pv.hist(which='total_cases',what='daily',option='nonneg',typeofhist='pie')
#pv.plot(which='total_cases',what='daily',option='nonneg')#,typeofhist='location')
#pv.setvis('matplotlib')
#pv.setbatch()
#pv.savefig('tata')
