.PHONY: test

test:
	nosetests -m'^$$' `find tests -name '*.py'`
