Deployment
----------

Create a Windows executable
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Python script wbcompute [#fn1]_ computes a waterbalance for a configuration
that is specified by a set of XML files. The script is written so users can
compute a waterbalance locally, that is, local on his (or her) computer,
without the dependency on the Django framework.

Unfurtunately, the user has some work cut out for him before he can actually
use the script: he has to setup the buildout environment. This means that he
needs a working Python 2.6.x or 2.7.x installation, he has to install Python
packages such as matplotlib and numpy globally, needs internet access and
finally, has to run buildout from the command-line.

To make it as easy for a user to use (but not develop) the script, we create a
stand-alone Windows executable using py2exe. This is a Python Distutils
extension which converts Python scripts into Windows executables that are able
to run without a Python installation and contain all dependencies.

To create such an executable for wbcompute, perform the following steps from
your buildout environment in Windows:

  1. Install py2exe. You can download the latest version from SourceForge at
  http://sunet.dl.sourceforge.net/project/py2exe/py2exe. Note that there are
  different versions for the different versions of Python.

  2. py2exe has to be able find the Python libraries the wbcompute script
  requires, which at the time of writing are the nens and timeseries libraries.
  We have to tell py2exe where it can find these libraries and we do that by
  adding them to the PYTHONPATH::

    C:\github.com\lizard-waterbalance>set PYTHONPATH=%PYTHONPATH%;C:\github.com\lizard-waterbalance\eggs\nens-1.10-py2.6.egg
    C:\github.com\lizard-waterbalance>set PYTHONPATH=%PYTHONPATH%;C:\github.com\lizard-waterbalance\eggs\timeseries-0.11-py2.6.egg

  You might wonder why we need to enhance the PYTHONPATH as buildout has
  already done that for us. That is true, but py2exe has no knowledge of the
  buildout environment. py2exe only uses the setup.py file of the script for
  which it has to create the executable.

  The following command::

    C:\github.com\lizard-waterbalance>C:\Python26\python.exe setup-wbcompute.py py2exe

  creates a ``dist\wbcompute.exe`` that contains the Python interpreter and all
  other dependencies.

.. rubric:: Footnotes

.. [#fn1] wbcompute is implemented by ``xmlmodel/wbcompute.py``
