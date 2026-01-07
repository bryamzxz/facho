#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of facho.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

# Dependencias minimas para la implementacion simplificada (sin zeep, xmlsig, xades)
# Estas son suficientes para usar facho.fe.builders y facho.fe.signing
requirements_minimal = [
    'Click>=6.0',
    'lxml>=5.0.0',
    'cryptography>=42.0.0',
    'requests>=2.28.0',
]

# Dependencias completas (compatibilidad con codigo existente)
requirements_legacy = [
    'chardet>=0.0',
    'zeep==4.2.1',
    'pyOpenSSL==24.1.0',
    'xmlsig==0.1.7',
    'xades==0.2.4',
    'xmlsec==1.3.14',
    # usamos esta dependencia en runtime
    # para forzar uso de policy_id de archivo local
    'mock>=2.0.0',
    'xmlschema>=1.8',
    'python-dateutil==2.9.0.post0',
]

# Por defecto, instalar todas las dependencias para compatibilidad
requirements = requirements_minimal + requirements_legacy

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

# Extras para instalacion selectiva
extras_require = {
    # Solo dependencias minimas (nueva implementacion simplificada)
    'minimal': [],  # Ya incluidas en requirements_minimal
    # Dependencias para codigo legacy (zeep, xmlsig, xades)
    'legacy': requirements_legacy,
    # Desarrollo
    'dev': ['pytest', 'pytest-cov', 'black', 'flake8'],
}

setup(
    author="Jovany Leandro G.C",
    author_email='bit4bit@riseup.net',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    description="Facturacion Electronica Colombia",
    entry_points={
        'console_scripts': [
            'facho=facho.cli:main',
        ],
    },
    install_requires=requirements,
    extras_require=extras_require,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/x-rst',
    include_package_data=True,
    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.gc', '*.xsd', 'politicadefirmav2.pdf']
    },
    keywords='facho',
    name='facho',
    packages=find_packages(exclude=("tests",)),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/bit4bit/facho',
    version='0.3.0',
    zip_safe=False,
)
