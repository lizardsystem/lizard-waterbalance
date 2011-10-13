lizard-waterbalance, branch VSS
===============================

This branch of lizard-waterbalance is used to split the current monolithic
Django application into three seperate components to configure the model,
compute the waterbalance and view the graphs.

The lizard-waterbalance master branch has a structure that looks like this::

  lizard-waterbalance/buildout.cfg
  lizard-waterbalance/...
  lizard-waterbalance/lizard-waterbalance/init.py
  lizard-waterbalance/lizard-waterbalance/models.py
  lizard-waterbalance/lizard-waterbalance/compute.py
  lizard-waterbalance/lizard-waterbalance/views.py

We agreed to move to a structure like the following::

  lizard-waterbalance/buildout.cfg
  lizard-waterbalance/...
  lizard-waterbalance/computation/init.py
  lizard-waterbalance/computation/compute.py
  lizard-waterbalance/visualization/init.py
  lizard-waterbalance/visualization/views.py
  lizard-waterbalance/lizard-waterbalance/init.py
  lizard-waterbalance/lizard-waterbalance/models.py

Then we will split off the different components into their own Git
repositories. To do so, we refer to http://stackoverflow.com/questions/359424

Usage, etc.

Development installation
------------------------

The first time, you'll have to run the "bootstrap" script to set up setuptools
and buildout::

    $> python bootstrap.py

And then run buildout to set everything up::

    $> bin/buildout

(On windows it is called ``bin\buildout.exe``).

You'll have to re-run buildout when you or someone else made a change in
``setup.py`` or ``buildout.cfg``.

The current package is installed as a "development package", so
changes in .py files are automatically available (just like with ``python
setup.py develop``).

If you want to use trunk checkouts of other packages (instead of released
versions), add them as an "svn external" in the ``local_checkouts/`` directory
and add them to the ``develop =`` list in buildout.cfg.

Tests can always be run with ``bin/test`` or ``bin\test.exe``.
