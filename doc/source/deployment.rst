Deployment
----------

Create a Windows executable
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Python script wbcompute [#fn1]_ computes a waterbalance for a configuration
that is specified by a set of XML files. The script is written so users can
compute a waterbalance locally, that is, local on his (or her) computer,
without the dependency on the Django framework.

Unfortunately, the user has some work cut out for him before he can actually
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
  requires, which at the time of writing are the pkginfo, nens and timeseries
  libraries.  We have to tell py2exe where it can find these libraries and we
  do that by adding them to the PYTHONPATH::

    C:\github.com\lizard-waterbalance>set PYTHONPATH=%PYTHONPATH%;C:\github.com\lizard-waterbalance\eggs\pkginfo-0.8-py2.6.egg
    C:\github.com\lizard-waterbalance>set PYTHONPATH=%PYTHONPATH%;C:\github.com\lizard-waterbalance\eggs\nens-1.10-py2.6.egg
    C:\github.com\lizard-waterbalance>set PYTHONPATH=%PYTHONPATH%;C:\github.com\lizard-waterbalance\eggs\timeseries-0.11-py2.6.egg

  You might wonder why we need to enhance the PYTHONPATH as buildout has
  already done that for us. That is true, but py2exe has no knowledge of the
  buildout environment. py2exe only uses the setup.py file of the script for
  which it has to create the executable.

  Note that the directories mentioned here are examples and the directories in
  your Windows environment might differ. You can find these directories in
  ``bin\buildout-script.py``.

  The following command::

    C:\github.com\lizard-waterbalance>C:\Python26\python.exe setup-wbcompute.py py2exe

  creates a ``dist\wbcompute.exe`` to use as an entry point for the wbcompute
  script. Note that you also have to place the other files from directory
  ``dist`` in the directory to which you deploy ``wbcompute.exe``.

py2exe byte-compiles the files of the libraries that wbcompute depends on and
packages these byte-compiled files. This also explains the need for a separate
setup for wbcompute: wbcompute uses only a small subset of the libraries the
Django app lizard-waterbalance uses. We want py2exe to only package those
libraries that are actually used.

On one occasion I noticed that it skipped the byte-compilation of a file whose
library had been updated. Consequently, the executable used an older version of
that file. I worked around this problem by deleting the directory that
setuptools uses to store its intermediate results, viz. subdirectory ``build``.

Create a tagged Windows executable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a releasable Windows executable, you have to create a tagged version
of the lizard-waterbalance Django app. As with all Python apps developed at
Nelen & Schuurmans, use the ``fullrelease`` script.

  1. Update the version info that is specified in the setup script of
  wbcompute. You have to do that manually as the fullrelease script only
  updates the version info in setup.py.

  2. Personally, I use my Ubuntu development environment to create a tagged
  version of the lizard-waterbalance Django app. From the root of the Django
  app do::

    bin/fullrelease

  Please note that if you create a release for a branch, e.g. the vss branch of
  lizard-waterbalance, you manually have to push the tag to GitHub.

  3. In your Windows development environment, switch to the newly created tag,
  e.g. from the root of the Django app do::

    git checkout <latest-tag-name>

  4. Before you can successfully run buildout, uncomment the ``sphinx`` part in
  ``buildout.cfg``, otherwise buildout will fail. Then execute::

    bin\buildout.exe

  5. Follow the steps mentioned in the previous section to create and package
  the Windows executable.


.. rubric:: Footnotes

.. [#fn1] wbcompute is implemented by ``xmlmodel/wbcompute.py``
