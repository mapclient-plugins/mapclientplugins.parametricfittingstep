import os
import io
from setuptools import setup, find_packages

SETUP_DIR = os.path.dirname(os.path.abspath(__file__))

# List all of your Python package dependencies in the
# requirements.txt file


def readfile(filename, split=False):
    with io.open(filename, encoding="utf-8") as stream:
        if split:
            return stream.read().split("\n")
        return stream.read()


readme = readfile("README.rst", split=True)[3:]  # skip title

# For requirements not hosted on PyPi place listings
# into the 'requirements.txt' file.
requires = ['get-image-size',
            'numpy']  # minimal requirements listing
source_license = readfile("LICENSE")


setup(
    name='mapclientplugins.parametricfittingstep',
    version='0.1.0',
    description='',
    long_description='\n'.join(readme) + source_license,
    classifiers=[
      "Development Status :: 3 - Alpha",
      "License :: OSI Approved :: Apache Software License",
      "Programming Language :: Python",
    ],
    author='Mahyar Osanlouy',
    author_email='m.osanlouy@auckland.ac.nz',
    url='',
    license='APACHE',
    packages=find_packages(exclude=['ez_setup',]),
    namespace_packages=['mapclientplugins'],
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
)
