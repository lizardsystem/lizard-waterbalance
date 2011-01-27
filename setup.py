from setuptools import setup

version = '0.4dev'

long_description = '\n\n'.join([
    open('README.txt').read(),
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
    'lizard-ui',
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
          ]},
      )
