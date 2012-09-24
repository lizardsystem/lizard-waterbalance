from setuptools import setup

version = '0.20.3'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('TODO.txt').read(),
    open('CREDITS.txt').read(),
    open('CHANGES.txt').read(),
    ])

install_requires = [
    'Django',
    'django-extensions',
    'django-nose',
    'django-staticfiles',
    'lizard-fewsunblobbed',
    'lizard-map',
    'lizard-shape',
    'lizard-ui > 1.53',
    'mock >= 0.7.2',
    'nens >= 1.10',
    'timeseries >= 0.11',
    'xlrd',
    'xlwt',
    'xlutils',
    ],

tests_require = [
    ]

setup(name='lizard-waterbalance',
      version=version,
      description="Django app to compute waterbalances",
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Programming Language :: Python',
                   'Framework :: Django',
                   ],
      keywords=[],
      author='P.C.J. Swinkels',
      author_email='pieter.swinkels@nelen-schuurmans.nl',
      url='',
      license='GPL3',
      packages=['lizard_waterbalance'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require = {'test': tests_require},
      entry_points={
          'console_scripts': [
              'wbcompute = xmlmodel.wbcompute:main',
              'check_symmetry = lizard_wbcomputation.check_symmetry:main',
              'check_fractions = lizard_wbcomputation.check_fractions:main',
              ],
          'lizard_map.adapter_class': [
              'adapter_waterbalance = lizard_waterbalance.layers:AdapterWaterbalance',
              ],
          },
      )
