.PHONY: test upload clean bootstrap

test:
	nosetests -m'^$$' `find tests -name '*.py'`
	
upload: README
	python setup.py sdist upload
	make clean
	
register:
	python setup.py register

README:
	pandoc --from=markdown --to=rst README.md > README

clean:
	rm -f README
	rm -f MANIFEST
	rm -rf dist
	
bootstrap: _virtualenv README
	_virtualenv/bin/pip install -e .
	_virtualenv/bin/pip install -r test-requirements.txt
	make clean
	
_virtualenv: 
	virtualenv _virtualenv
