all: test-import-excel

test-import-excel:
	../bin/django sqlreset lizard_waterbalance | grep -o "DROP TABLE.*;" | sed "s/\(.*\);/\1;/" | ../bin/django dbshell
	../bin/django syncdb --noinput
	../bin/django import_excel import-excel
	../bin/django dumpdata --indent=2 lizard_waterbalance > import-excel/lizard_waterbalance.json
	diff import-excel/expected_lizard_waterbalance.json import-excel/lizard_waterbalance.json