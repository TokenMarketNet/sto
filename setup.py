#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()


requirements = [
    'web3',
    'coloredlogs',
]

test_requirements = [
    'pytest',

]

dev_requirements = [
]

setup(
    name='corporategovernance',
    version='0.1',
    description="Corporate governance tools for tokenised stock",
    long_description=readme + '\n\n',
    author="TokenMarket Ltd.",
    author_email='mikko@tokenmarket.net',
    url='https://tokenmarket.net',
    packages=[
        'corporategovernance',
    ],
    package_dir={'corporategovernance':
                 'corporategovernance'},
    include_package_data=True,
    install_requires=requirements,
    license="Apache 2.0",
    zip_safe=False,
    keywords='ethereum blockchain smartcontract security token',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    setup_requires=["pytest-runner"],
    tests_require=test_requirements,
    entry_points='''
    [console_scripts]
    board=corporategovernance.cli.main:main
    ''',
)
