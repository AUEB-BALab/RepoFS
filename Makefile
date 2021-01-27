test:
	./repofs/tests/make_test_repo.sh
	python3 -m unittest discover -s repofs/tests -p *_test.py
