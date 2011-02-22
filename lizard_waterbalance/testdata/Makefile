large: clean
	time ../../../../bin/django compute_waterbalance . aetsveldsche-polder-oost 1996-01-01 2010-06-30
	diff intermediate-results.csv expected-intermediate-results.csv
	diff Bastiaan-results.csv expected-Bastiaan-results.csv
	diff waterbalance-outcome.csv expected-waterbalance-outcome.csv

small:
	diff intermediate-small-results.csv expected-intermediate-small-results.csv
	diff Bastiaan-small-results.csv expected-Bastiaan-small-results.csv

update:
	cp intermediate-results.csv expected-intermediate-results.csv
	cp Bastiaan-results.csv expected-Bastiaan-results.csv
	cp waterbalance-outcome.csv expected-waterbalance-outcome.csv

update-small:
	cp intermediate-small-results.csv expected-intermediate-small-results.csv
	cp Bastiaan-small-results.csv expected-Bastiaan-small-results.csv

clean:
	-rm intermediate-results.csv
	-rm Bastiaan-results.csv
	-rm waterbalance-outcome.csv

clean-small:
	-rm intermediate-small-results.csv
	-rm Bastiaan-small-results.csv
