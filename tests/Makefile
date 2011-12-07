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
	cd waterbalance-output-Aetsveldse-polder; rm sluice-error.xml
	cd waterbalance-output-Aetsveldse-polder; rm open-water-incoming-flows.xml
	cd waterbalance-output-Aetsveldse-polder; rm open-water-outgoing-flows.xml
	cd waterbalance-output-Aetsveldse-polder; rm level-control-timeseries.xml
	cd waterbalance-output-Aetsveldse-polder; rm reference.xml
	cd waterbalance-output-Aetsveldse-polder; rm water-level-sluice-error.xml
	cd waterbalance-output-Aetsveldse-polder; rm fractions.xml
	cd waterbalance-output-Aetsveldse-polder; rm concentration.xml
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
	cd waterbalance-output-Aetsveldse-polder; rm impact.xml
	cd waterbalance-output-Aetsveldse-polder; rm impact-incremental.xml
	cd waterbalance-output-Aetsveldse-polder; ../../bin/django compute_export aetsveldse-polder-oost import export-impact-all
	cd waterbalance-output-Aetsveldse-polder; diff expected-impact.xml impact.xml
	cd waterbalance-output-Aetsveldse-polder; diff expected-impact-incremental.xml impact-incremental.xml

test-waterbalance-output-impact-open-water:
	cd waterbalance-output-Aetsveldse-polder; rm impact-open-water.xml
	cd waterbalance-output-Aetsveldse-polder; rm impact-incremental-open-water.xml
	cd waterbalance-output-Aetsveldse-polder; ../../bin/django compute_export aetsveldse-polder-oost import export-impact-open-water
	cd waterbalance-output-Aetsveldse-polder; diff expected-impact-open-water.xml impact-open-water.xml
	cd waterbalance-output-Aetsveldse-polder; diff expected-impact-incremental-open-water.xml impact-incremental-open-water.xml
