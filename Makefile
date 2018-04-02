test:
	./repofs/tests/make_test_repo.sh
	python -m unittest discover -s repofs/tests -p *_test.py
