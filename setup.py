from setuptools import setup, find_packages

setup(
    name="pyvoa",  
    version="0.2.1",  
    author="pyvoa.org",
    author_email="support@pyvoa.org",
    description="Python virus open analysis. See more on pyvoa.org",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/pyvoa/pyvoa",  # Link to github deposit
    packages=find_packages(), 
    package_data={'pyvoa' :['data/*.json']},
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
        "importlib",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",  # Version minimale de Python
)
