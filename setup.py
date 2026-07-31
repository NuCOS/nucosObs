#!/usr/bin/env python

from pathlib import Path

from setuptools import find_packages, setup

NAME = "nucosObs"
ROOT = Path(__file__).parent

version_namespace = {}
exec((ROOT / NAME / "version.py").read_text(), version_namespace)

setup(name=NAME,
      version=version_namespace["version"],
      description='nucosObs - an observer/observable toolbox based on asyncio',
      long_description=(ROOT / "README.md").read_text(),
      long_description_content_type="text/markdown",
      url='https://github.com/DocBO/nucosObs',
      author='Oliver Braun',
      author_email='oliver.braun@nucos.de',
      license='MIT',
      # https://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          'Development Status :: 1 - Planning',
          'Environment :: Console',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
                    'Programming Language :: Python :: 3.11',
                    'Programming Language :: Python :: 3.12',
                    'Programming Language :: Python :: 3.13'
      ],
      keywords='observer observable asyncio',
            python_requires='>=3.9',
            packages=find_packages(include=["nucosObs", "nucosObs.*"]),
            install_requires=['websockets>=15,<16', 'aiohttp>=3.12,<4'],
            extras_require={
                    "test": [
                            "pytest>=8,<9; python_version < '3.10'",
                            "pytest>=9,<10; python_version >= '3.10'",
                            "pytest-asyncio>=0.23,<1; python_version < '3.10'",
                            "pytest-asyncio>=1,<2; python_version >= '3.10'",
                    ],
            },
      )
