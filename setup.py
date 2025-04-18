from setuptools import setup
from Cython.Build import cythonize
from glob import glob 
files = glob("*.py")
targetf = [f for f in files if f not in ["setup.py","yt-worker.py","ke-server.py"]]
setup(ext_modules=cythonize(targetf))
