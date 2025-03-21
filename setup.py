from setuptools import setup, find_packages

try:
    importlib.import_module("bokeh")
    include_visu_bokeh = True
except ImportError:
    include_visu_bokeh = False

# Définir les fichiers à inclure
package_files = ["pyvoa/*.py"]
if include_visu_bokeh:
    package_files.append("pyvoa/visu_bokeh.py")


setup(
    name="pyvoa",  
    version="0.2.2",  
    author="pyvoa.org",
    author_email="support@pyvoa.org",
    description="Python virus open analysis. See more on pyvoa.org",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/pyvoa/pyvoa",  # Link to github deposit
    packages=find_packages(), 
    package_data={'pyvoa' :['data/*.json',package_files]},
    install_requires=[
        "pandas",
        "geopandas",
        "shapely",
        "bs4",
        "numpy",
        "pycountry",
        "pycountry_convert",
        "requests",
        "unidecode",
        "lxml",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",  # Version minimale de Python
)
