from setuptools import setup, find_packages


with open('README.rst') as readme_file:
    readme = readme_file.read()


requirements = [
    'eth-typing<2',
    'eth-abi<1.3',
    'web3[tester]',  # Cannot have more specific web3 settings separately in test_requirements
    'coloredlogs',
    'colorama',
    'tabulate',
    'sqlalchemy>=1.3.0b1',
    'tqdm',
    'configobj',
    'click',
    'arrow',
    'pysha3<2.0.0',
]

test_requirements = [
    'pytest',
]

dev_requirements = [
    "bumpversion>=0.5.3,<1",
    "wheel",
    "sphinx",
    "sphinx_rtd_theme==0.4.2",
    "setuptools",
]

setup(
    name='sto',
    version='0.4.0',
    description="Security token manager",
    long_description=readme + '\n\n',
    author="TokenMarket Ltd.",
    author_email='mikko@tokenmarket.net',
    url='https://docs.tokenmarket.net',
    #packages=[
    #    'sto',
    #],
    #package_dir={'sto':
    #             'sto'},
    #include_package_data=True,
    packages=find_packages(exclude=['docs', 'tests', 'venv', 'venv2', '.*']),
    install_requires=requirements,
    license="Apache 2.0",
    zip_safe=False,
    keywords='ethereum blockchain smartcontract security token',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    setup_requires=["pytest-runner"],
    extras_require={
        "test": test_requirements,
        "dev": dev_requirements,
    },
    entry_points='''
    [console_scripts]
    sto=sto.cli.main:main
    ''',
)
