#!/usr/bin/env python

import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='whack',
    version='0.7.0',
    description='Utility for installing binaries from source with a single command',
    long_description=read("README.rst"),
    author='Michael Williamson',
    url='http://github.com/mwilliamson/whack',
    scripts=["scripts/whack"],
    packages=['whack'],
    install_requires=[
        'mayo>=0.2.1,<0.3',
        'requests>=1,<2',
        "catchy>=0.2.0,<0.3",
        "beautifulsoup4>=4.1.3,<5",
        "spur.local>=0.3.6,<0.4",
        "dodge>=0.1.5,<0.2",
        "six>=1.4.1,<2.0"
    ],
)
