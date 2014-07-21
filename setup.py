#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='namesync',
    version='0.2',
    packages=['namesync'],
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
    test_suite='tests',
    test_loader='unittest:TestLoader',
)
