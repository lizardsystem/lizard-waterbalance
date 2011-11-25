VSS branch of lizard-waterbalance
---------------------------------

lizard-waterbalance is a Django application to store configurations of
waterbalance models and to compute and visualize the waterbalance of a specific
configuration. The master branch at GitHub implements all these functionalities
within a single Python package, viz. lizard_waterbalance. We have created this
branch to separate the functionality to compute a waterbalance from the
functionality to store and view one.

lizard-waterbalance consists of the following Python packages:

lizard_waterbalance
  defines and manages the database objects that specify implement multiple
  waterbalance configurations and visualizes a waterbalance

lizard_wbcomputation
  computes a waterbalance for a given waterbalance configuration

dbmodels
  provides a waterbalance configuration that wraps the objects of a Django
  database

xmlmodels
  provides a waterbalance configuration that wraps the information stored in
  XML files

For now, these packages are all part of the same Django application. In the
end, we will split off lizard_wbcomputation and xmlmodels into their own Git
repositories. To do so, we refer to http://stackoverflow.com/questions/359424


Setup development environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The first time, you'll have to run the "bootstrap script" to set up setuptools
and buildout::

    $> python bootstrap.py

And then run buildout to set everything up::

    $> bin/buildout

On windows it is called ``bin\buildout.exe``. Note that on Windows, we had to
remove the ``sphinx`` part from buildout.cfg as buildout aborted when it wanted
to create the Sphinx environment.

You'll have to re-run buildout when you or someone else made a change in
``setup.py`` or ``buildout.cfg``.

The current package is installed as a "development package", so
changes in .py files are automatically available (just like with ``python
setup.py develop``).

If you want to use trunk checkouts of other packages (instead of released
versions), add them as an "svn external" in the ``local_checkouts/`` directory
and add them to the ``develop =`` list in buildout.cfg.

Tests can always be run with ``bin/test`` or ``bin\test.exe``.
