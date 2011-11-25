Scripts and management commands
-------------------------------

In this chapter we describe the various command-line scripts and management
commands that are provided by lizard-waterbalance.

wbcompute
~~~~~~~~~

Script ``wbcompute`` computes a waterbalance for a configuration that is
specified by three distinct XML files, viz.

  - a "parameters" file, which specifies the entities of the waterbalance
    model. Examples of such entities are buckets and pumping stations.
  - a "tijdreeksen" file, which specifies the time series. Examples of such
    time series are the precipitation, seepage and intake discharge time
    series.
  - a "run" file, which specifies general parameters for the management
    command.

A complete example of these XMLs file can be found `here
<https://github.com/lizardsystem/lizard-waterbalance/tree/vss/data/deltares>`_.

An example run file looks like this::

  <?xml version="1.0" encoding="UTF-8"?>
  <Run xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.wldelft.nl/fews/PI" xsi:schemaLocation="http://www.wldelft.nl/fews/PI http://fews.wldelft.nl/schemas/version1.0/pi-schemas/pi_run.xsd" version="1.5">
      <timeZone>1.0</timeZone>
      <startDateTime date="2000-01-01" time="00:00:00"/>
      <endDateTime date="2010-01-01" time="00:00:00"/>
      <time0 date="2010-01-01" time="00:00:00"/>
      <workDir>D:\FEWS_Systemen\KRW_VSS\KRW_VSS\Modules\Waterbalans\Waterbalans\model</workDir>
      <inputParameterFile>D:\FEWS_Systemen\KRW_VSS\KRW_VSS\Modules\Waterbalans\Waterbalans\input\Parameters.xml</inputParameterFile>
      <inputTimeSeriesFile>D:\FEWS_Systemen\KRW_VSS\KRW_VSS\Modules\Waterbalans\Waterbalans\input\Tijdreeksen.xml</inputTimeSeriesFile>
      <outputDiagnosticFile>D:\FEWS_Systemen\KRW_VSS\KRW_VSS\Modules\Waterbalans\Waterbalans\Diagnostics\Diagnostics.xml</outputDiagnosticFile>
      <outputTimeSeriesFile>D:\FEWS_Systemen\KRW_VSS\KRW_VSS\Modules\Waterbalans\Waterbalans\output\waterbalance-graph.xml</outputTimeSeriesFile>
      <properties>
          <string key="Regio" value="Waternet"/>
          <string key="Gebied" value="SAP"/>
      </properties>
  </Run>

The script uses the following settings from this file:

  - ``startDateTime`` and ``endDateTime`` for the first and last date for which to
    compute the waterbalance;
  - ``inputParameterFile`` for the path to the parameter file;
  - ``outputParameterFile`` for the path to the tijdreeksen file;
  - ``outputTimeSeriesFile`` for the path to the file that will contain the
    computed time series;
  - ``outputDiagnosticsFile`` for the path to the file that will contain the
    log.

In the example above the log file is specified as an XML file. Note that at the
moment, the log file does not have to be an XML file.

The script will ignore all the other information in the run file.

The user can invoke the script from the lizard-waterbalance root directory like
this [#fn1]_::

  $> bin/wbcompute <path-to-the-run-xml-file>

The command will compute the waterbalance for the configuration specified in
the given run file.

.. rubric:: Footnotes

.. [#fn1] the command-line interface of wbcompute.exe is the same
