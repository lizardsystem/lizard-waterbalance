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