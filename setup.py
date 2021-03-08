from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    'arrow',
    'click',
    'colorama',
    'coloredlogs',
    'configobj',
    'pysha3',
    'sqlalchemy',
    'tabulate',
    'tqdm',
    'web3>5',
]

test_requirements = [
    'pytest',
    'tox',
]

dev_requirements = [
    "bumpversion>=0.5.3,<1",
    "wheel",
    "setuptools",
]

setup(
    name='tokfetch',
    version='0.0.1',
    description="Token balance manager",
    long_description=readme + '\n\n',
    author="Illia Likhoshva",
    author_email='ilyaliko64@gmail.com',
    url='https://github.com/LikoIlya/tokfetch',
    # packages=[
    #    'tokfetch',
    # ],
    # package_dir={'tokfetch':
    #             'tokfetch'},
    # include_package_data=True,
    packages=find_packages(exclude=['docs', 'tests', 'venv', 'venv2', '.*']),
    install_requires=requirements,
    license="Apache 2.0",
    zip_safe=False,
    keywords='ethereum blockchain heco smartcontract token erc20 hrc20',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],
    test_suite='tests',
    setup_requires=["pytest-runner"],
    extras_require={
        "test": test_requirements,
        "dev": dev_requirements,
    },
    entry_points='''
    [console_scripts]
    tokfetch=tokfetch.cli.main:main
    ''',
)
