#!/usr/bin/env python
from __future__ import print_function

import os
import sys

from setuptools import setup, find_packages
import unittest

name = "nucosObs"

rootdir = os.path.abspath(os.path.dirname(__file__))

long_description = """

Dokumentation: [http://nucosObs.readthedocs.io/]

"""

# Python 3.5 or later needed
if sys.version_info < (3, 5, 0, 'final', 0):
    raise SystemExit('Python 3.5 or later is required!')

# Build a list of all project modules
packages = []
for dirname, dirnames, filenames in os.walk(name):
        if '__init__.py' in filenames:
            packages.append(dirname.replace('/', '.'))

package_dir = {name: name}

# Data files used e.g. in tests
package_data = {} #{name: [os.path.join(name, 'tests', 'prt.txt')]}

# The current version number - MSI accepts only version X.X.X
exec(open(os.path.join(name, 'version.py')).read())

print("Version:", version)

# Scripts
scripts = []
for dirname, dirnames, filenames in os.walk('scripts'):
    for filename in filenames:
        if not filename.endswith('.bat'):
            scripts.append(os.path.join(dirname, filename))

# Provide bat executables in the tarball (always for Win)
if 'sdist' in sys.argv or os.name in ['ce', 'nt']:
    for s in scripts[:]:
        scripts.append(s + '.bat')

# Data_files (e.g. doc) needs (directory, files-in-this-directory) tuples
data_files = []
for dirname, dirnames, filenames in os.walk('doc'):
        fileslist = []
        for filename in filenames:
            fullname = os.path.join(dirname, filename)
            fileslist.append(fullname)
        data_files.append(('share/' + name + '/' + dirname, fileslist))

setup(name=name,
      version=version,  # PEP440
      description='nucosObs - an observer/observable toolbox based on asyncio',
      long_description=long_description,
      url='https://github.com/DocBO/nucosObs',
      download_url = 'https://github.com/DocBO/nucosObs/tarball/0.0.1',
      author='Oliver Braun',
      author_email='oliver.braun@nucos.de',
      license='MIT',
      # https://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          'Development Status :: 1 - Planning',
          'Environment :: Console',
          'License :: OSI Approved :: MIT License',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
      ],
      keywords='observer observable asyncio',
      packages=packages,
      package_dir=package_dir,
      package_data=package_data,
      scripts=scripts,
      install_requires=['websockets']
      )
