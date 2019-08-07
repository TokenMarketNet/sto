from setuptools import setup, find_packages


with open('README.rst') as readme_file:
    readme = readme_file.read()


# We have known dependency issues with v4 tester. It used to be that on install, it threw an error, but still worked anyway. I think you should be able to use eth-abi 1.3 even though it complains

requirements = [
    'web3<5',
    # 'eth-typing==',
    # 'eth-utils',
    # 'eth-abi',

    # Your everyday upstream Ooops we broke dependencies again making everything uninstallable
    "eth-abi==1.2.2",
    "eth-account==0.3.0",
    "eth-bloom==1.0.1",
    "eth-hash==0.2.0",
    "eth-keyfile==0.5.1",
    "eth-keys==0.2.0b3",
    "eth-rlp==0.1.2",
    "eth-tester==0.1.0b33",
    "eth-typing==1.3.0",
    "eth-utils==1.3.0",
    "py-ecc==1.4.3",
    "py-evm==0.2.0a33",
    "py-geth==2.0.1",

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
    '',
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
    version='0.4.1',
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
