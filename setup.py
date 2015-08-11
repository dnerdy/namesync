#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

VERSION='0.4'

setup(
    name='namesync',
    version=VERSION,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    description='Sync DNS records stored in a flat file format to your DNS provider.',
    author='Mark Sandstrom',
    author_email='mark@deliciouslynerdy.com',
    url='https://github.com/dnerdy/namesync',
    download_url='https://github.com/dnerdy/namesync/archive/v{}.tar.gz'.format(VERSION),
    setup_requires=[
        'setuptools>=0.8',
    ],
    install_requires=[
        'requests==2.2.1',
    ],
    entry_points={
        'console_scripts': [
            'namesync = namesync.main:main',
        ],
    },
    test_suite='nose.collector',
    test_loader='unittest:TestLoader',
    keywords=['dns', 'sync', 'syncing', 'cloudflare'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Topic :: Internet :: Name Service (DNS)",
    ],
)
