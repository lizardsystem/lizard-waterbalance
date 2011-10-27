all: test-import-excel test-import-excel-Sierveld-20110916

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
	cd ..; bin/django compute_export aetsveldse-polder-oost import
	diff expected-sluice-error.xml ../sluice-error.xml
	diff expected-open-water-incoming-flows.xml ../open-water-incoming-flows.xml
	diff expected-open-water-outgoing-flows.xml ../open-water-outgoing-flows.xml
	diff expected-level-control-timeseries.xml ../level-control-timeseries.xml
	diff expected-reference.xml ../reference.xml
	diff expected-water-level-sluice-error.xml ../water-level-sluice-error.xml
	diff expected-fractions.xml ../fractions.xml