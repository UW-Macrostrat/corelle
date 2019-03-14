from setuptools import setup

setup(
    name='corelle',
    version='0.1',
    package_dir={'corelle': 'corelle'},
    entry_points={
          'console_scripts': ['plates = corelle.cli:cli']
    }
)
