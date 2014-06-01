#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from pip.req import parse_requirements
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')
install_reqs = parse_requirements('requirements.txt')
requirements = [str(ir.req) for ir in install_reqs]

setup(
    name='ddlgenerator',
    version='0.1.1',
    description='Generates SQL DDL that will accept Python data',
    long_description=readme + '\n\n' + history,
    author='Catherine Devlin',
    author_email='catherine.devlin@gmail.com',
    url='https://github.com/catherinedevlin/ddlgenerator',
    packages=[
        'ddlgenerator',
    ],
    package_dir={'ddlgenerator': 'ddlgenerator'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='ddlgenerator',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'ddlgenerator = ddlgenerator.console:generate',
        ]
    }
)
