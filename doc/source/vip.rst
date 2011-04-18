Most important classes
======================

Computation
-----------

The class WaterbalanceComputer is the main interface to the functionality of
the lizard_waterbalance application and especially its method 'compute':

.. automethod:: lizard_waterbalance.compute.WaterbalanceComputer2.compute

A BucketOutcome contains all the timeseries that are computed for a single Bucket:

.. autoclass:: lizard_waterbalance.bucket_computer.BucketOutcome

Caching
-------

To compute the information to display a 'pure' waterbalance graph takes about
20 seconds [#f1]_, which is including the time needed to retrieve the data from
the database. The user has to wait those 20 seconds each time the graph has to
be displayed or redisplayed, for example when he resizes the browser window. To
reduce the waiting time, we cache the outcome of the calls to a
WaterbalanceComputer. This is implemented by class CachedWaterbalanceComputer,
which is a subclass of WaterbalanceComputer:

.. autoclass:: lizard_waterbalance.views.CachedWaterbalanceComputer

This works very effectively. For example, to show the 'pure' waterbalance graph
using `memcached <http://memcached.org/>`_, the time to retrieve the required
information is reduced from 20 to 2 seconds.

The waiting time could be reduced even further. The data that is cached in the
view is used to compute the data display the graphs. If we cache the data to
display the graph directly, we avoid an additional computation step and often
we have to store less data. For example, a time series that is the outcome of a
call to a WaterbalanceComputer specifies a value for each day. In general, the
user wants to see a graph that aggregates the values for each month. If we
would cache these monthly values, we avoid the aggregation step and only have a
thirtieth of the data to retrieve from the cache [#f2]_.


.. [#f1] measured on a Lenovo ThinkPad Edge using an Intel Core i5 at 2.27 GHz
         with 3.7 GB internal memory and running Ubuntu 10.04

.. [#f2] this suggestion has been registered as `ticket 2568 <https://office.nelen-schuurmans.nl/trac/ticket/2568>`_
