import pyvoa
from importlib.resources import files, as_file
import os

data_filename=files(pyvoa).joinpath('data/spf.json')
print(os.path.exists(data_filename))
