all: test-import-excel test-import-excel-Sierveld-20110916		\
	test-waterbalance-output test-waterbalance-output-impact-all	\
	test-waterbalance-output-impact-open-water

test-import-excel:
	../bin/django sqlreset lizard_waterbalance | grep -o "DROP TABLE.*;" | sed "s/\(.*\);/\1;/" | ../bin/django dbshell
	../bin/django syncdb --noinput
	../bin/django import_excel import-excel
	../bin/django dumpdata --indent=2 lizard_waterbalance > import-excel/lizard_waterbalance.json
	diff -q import-excel/expected_lizard_waterbalance.json import-excel/lizard_waterbalance.json

test-import-excel-Sierveld-20110916:
	../bin/django sqlreset lizard_waterbalance | grep -o "DROP TABLE.*;" | sed "s/\(.*\);/\1;/" | ../bin/django dbshell
	../bin/django syncdb --noinput
	../bin/django import_excel import-excel-Sierveld-20110916
	../bin/django dumpdata --indent=2 lizard_waterbalance > import-excel-Sierveld-20110916/lizard_waterbalance.json
	diff -q import-excel-Sierveld-20110916/expected_lizard_waterbalance.json import-excel-Sierveld-20110916/lizard_waterbalance.json

test-waterbalance-output:
	- rm waterbalance-output-Aetsveldse-polder/sluice-error.xml
	- rm waterbalance-output-Aetsveldse-polder/open-water-incoming-flows.xml
	- rm waterbalance-output-Aetsveldse-polder/open-water-outgoing-flows.xml
	- rm waterbalance-output-Aetsveldse-polder/level-control-timeseries.xml
	- rm waterbalance-output-Aetsveldse-polder/reference.xml
	- rm waterbalance-output-Aetsveldse-polder/water-level-sluice-error.xml
	- rm waterbalance-output-Aetsveldse-polder/fractions.xml
	- rm waterbalance-output-Aetsveldse-polder/concentration.xml
	cd waterbalance-output-Aetsveldse-polder; ../../bin/django compute_export aetsveldse-polder-oost import
	cd waterbalance-output-Aetsveldse-polder; diff expected-sluice-error.xml sluice-error.xml
	cd waterbalance-output-Aetsveldse-polder; diff expected-open-water-incoming-flows.xml open-water-incoming-flows.xml
	cd waterbalance-output-Aetsveldse-polder; diff expected-open-water-outgoing-flows.xml open-water-outgoing-flows.xml
	cd waterbalance-output-Aetsveldse-polder; diff expected-level-control-timeseries.xml level-control-timeseries.xml
	cd waterbalance-output-Aetsveldse-polder; diff expected-reference.xml reference.xml
	cd waterbalance-output-Aetsveldse-polder; diff expected-water-level-sluice-error.xml water-level-sluice-error.xml
	cd waterbalance-output-Aetsveldse-polder; diff expected-fractions.xml fractions.xml
	cd waterbalance-output-Aetsveldse-polder; diff expected-concentration.xml concentration.xml

test-waterbalance-output-impact-all:
	- rm waterbalance-output-Aetsveldse-polder/impact.xml
	- rm waterbalance-output-Aetsveldse-polder/impact-incremental.xml
	cd waterbalance-output-Aetsveldse-polder; ../../bin/django compute_export aetsveldse-polder-oost import export-impact-all
	cd waterbalance-output-Aetsveldse-polder; diff expected-impact.xml impact.xml
	cd waterbalance-output-Aetsveldse-polder; diff expected-impact-incremental.xml impact-incremental.xml

test-waterbalance-output-impact-open-water:
	- rm waterbalance-output-Aetsveldse-polder/impact-open-water.xml
	- rm waterbalance-output-Aetsveldse-polder/impact-incremental-open-water.xml
	cd waterbalance-output-Aetsveldse-polder; ../../bin/django compute_export aetsveldse-polder-oost import export-impact-open-water
	cd waterbalance-output-Aetsveldse-polder; diff expected-impact-open-water.xml impact-open-water.xml
	cd waterbalance-output-Aetsveldse-polder; diff expected-impact-incremental-open-water.xml impact-incremental-open-water.xml

test-increment-2:
	- rm increment-2/nan/output/waterbalance-graph.xml
	../bin/wbcompute increment-2/nan/input/Run.xml
	python verify_presence.py increment-2/nan/output/waterbalance-graph.xml 'value="nan"'
	- rm increment-2/nan-2/output/waterbalance-graph.xml
	../bin/wbcompute increment-2/nan-2/input/Run.xml
	python verify_presence.py increment-2/nan-2/output/waterbalance-graph.xml 'value="nan"'
