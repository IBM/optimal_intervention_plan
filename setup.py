#!/usr/bin/env python

##################################################################
#
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2020. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
##################################################################

from setuptools import setup, find_packages
import sys


def python_version_requirements():
    """
    Returns the list of package dependencies for the respective version of Python
    :return:
    """
    if sys.version_info >= (3, 7):
        # Python 3.7 requirements
        return [
            'future==0.16.0',
            'numpy==1.15.1',
            'ujson==1.35',
            'simplejson==3.13.2',
            'docloud==1.0.375',
            'docplex==2.13.184',
            'ibmdbpy==0.1.6',
            'jaydebeapi==1.1.1',
        ]
    else:
        raise EnvironmentError('Unsupported Python version')

setup(
    name='resop',
    version='0.0.2',
    description='Resource optimization utilities',
    long_description='This package contains utilities for obtaining optimized allocation of resources given an objective.',
    author='Hamideh Anjomshoa, Roslyn Hicks, Stefan von Cavallar, Olivia Smith', 'Manoj Gambhir',
    author_email='hamideh.a@au1.ibm.com, svcavallar@au1.ibm.com
    url='https://github.ibm.com/Hamideh-A/optimal_intervention_plan',
    install_requires=python_version_requirements(),
    extras_require={
        'dev': [],
        'test': ['flake8', 'pytest', 'coverage'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering'],
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    license='Apache'
)