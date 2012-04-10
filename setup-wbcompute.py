from setuptools import setup

import py2exe

version = '0.19.1.23dev'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('TODO.txt').read(),
    open('CREDITS.txt').read(),
    open('CHANGES.txt').read(),
    ])

install_requires = [
    'nens == 1.10',
    'timeseries == 0.17',
    ],

tests_require = [
    ]

setup(name='lizard-waterbalance',
      version=version,
      description="Python script to compute waterbalances",
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Programming Language :: Python'],
      keywords=[],
      author='Nelen & Schuurmans',
      author_email='pieter.swinkels@nelen-schuurmans.nl',
      url='',
      license='GPL3',
      packages=['lizard_waterbalance'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require = {'test': tests_require},
      console = ['xmlmodel/wbcompute.py'],
      entry_points={
          'console_scripts': [
              'wbcompute = xmlmodel.wbcompute:main',
              ],
          },
      )
