#!/usr/bin/env python
from setuptools import setup, find_packages
from xcat import version

setup(
    name="xcat",
    version=version,
    entry_points = {
    "console_scripts": ['xcat = xcat.cli:main']
    },
    description="Xcat is a package that creates cross-chain atomic transactions.",
    author="arcalinea and arielgabizon",
    author_email="arcalinea@z.cash",
    license="MIT",
    url="http://github.com/zcash/xcat",
    install_requires=['python-bitcoinlib', 'plyvel'],
    dependency_links=['http://github.com/arcalinea/python-zcashlib/tarball/master'],
    packages=find_packages()
)
