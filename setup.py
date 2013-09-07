#!/usr/bin/env python

import os
import sys
from setuptools import setup

extra = {}
if sys.version_info >= (3, 0):
    extra["use_2to3"] = True


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='whack',
    version='0.7.0',
    description='Utility for installing binaries from source with a single command',
    long_description=read("README"),
    author='Michael Williamson',
    url='http://github.com/mwilliamson/whack',
    scripts=["scripts/whack"],
    packages=['whack'],
    install_requires=[
        'mayo>=0.2.1,<0.3',
        'requests>=1,<2',
        "catchy>=0.2.0,<0.3",
        "beautifulsoup4>=4.1.3,<5",
        "spur.local>=0.3.2,<0.4",
        "dodge>=0.1.4,<0.2",
    ],
    **extra
)
