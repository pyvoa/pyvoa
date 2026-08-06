import os
from importlib.resources import files

import pyvoa

data_filename=files(pyvoa).joinpath('data/spf.json')
print(os.path.exists(data_filename))
